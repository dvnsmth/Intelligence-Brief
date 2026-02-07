"""
Normalization pipeline: language detection, translation, entity recognition,
and story clustering/deduplication.
"""

import re
from typing import List, Dict, Set
from datetime import datetime, timedelta
import hashlib

try:
    from langdetect import detect, LangDetectException
except ImportError:
    # Fallback if langdetect not available
    def detect(text):
        return 'en'

try:
    from googletrans import Translator
except ImportError:
    Translator = None

from .models import RawSource, Entity, EntityType
from .config import get_config


class NormalizationPipeline:
    """Pipeline for normalizing raw sources"""
    
    def __init__(self):
        self.config = get_config()
        self.translator = Translator() if Translator else None
        self.country_names = self._load_country_names()
    
    def normalize(self, sources: List[RawSource]) -> List[RawSource]:
        """Normalize a list of sources"""
        normalized = []
        for source in sources:
            try:
                norm_source = self._normalize_source(source)
                normalized.append(norm_source)
            except Exception as e:
                print(f"Error normalizing source {source.source_id}: {e}")
                continue
        return normalized
    
    def _normalize_source(self, source: RawSource) -> RawSource:
        """Normalize a single source"""
        # Detect language if not already detected
        if source.language == 'en' or not source.language:
            try:
                detected = detect(source.content[:500])  # Sample for speed
                source.language = detected
            except (LangDetectException, Exception):
                source.language = 'en'
        
        # Translate to English if needed (for MVP, skip translation if not available)
        # In production, this would translate non-English content
        
        return source
    
    def extract_entities(self, source: RawSource) -> List[Entity]:
        """Extract entities from a source"""
        entities = []
        text = f"{source.title} {source.content}"
        
        # Extract countries
        countries = self._extract_countries(text)
        for country in countries:
            entity = Entity(
                entity_id=self._generate_entity_id(country, EntityType.COUNTRY),
                entity_type=EntityType.COUNTRY,
                canonical_name=country,
                geo_scope=country,
                confidence=0.8
            )
            entities.append(entity)
        
        return entities
    
    def _extract_countries(self, text: str) -> Set[str]:
        """Extract country names from text"""
        found = set()
        text_lower = text.lower()
        
        for country in self.country_names:
            # Simple pattern matching
            pattern = r'\b' + re.escape(country.lower()) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.add(country)
        
        return found
    
    def cluster_sources(self, sources: List[RawSource]) -> List[List[RawSource]]:
        """Cluster similar sources to prevent duplication"""
        clusters = []
        processed = set()
        
        # Group by time window
        time_window = timedelta(hours=self.config.deduplication.time_window_hours)
        
        # Sort by time
        sorted_sources = sorted(sources, key=lambda s: s.published_at or s.retrieved_at)
        
        for source in sorted_sources:
            if source.source_id in processed:
                continue
            
            # Start new cluster
            cluster = [source]
            processed.add(source.source_id)
            
            # Find similar sources
            for other in sorted_sources:
                if other.source_id in processed:
                    continue
                
                if self._are_similar(source, other, time_window):
                    cluster.append(other)
                    processed.add(other.source_id)
            
            clusters.append(cluster)
        
        return clusters
    
    def _are_similar(self, source1: RawSource, source2: RawSource, time_window: timedelta) -> bool:
        """Check if two sources are similar enough to cluster"""
        # Time window check
        time1 = source1.published_at or source1.retrieved_at
        time2 = source2.published_at or source2.retrieved_at
        
        if abs((time1 - time2).total_seconds()) > time_window.total_seconds():
            return False
        
        # Title similarity (simple)
        title_sim = self._text_similarity(source1.title, source2.title)
        if title_sim > self.config.deduplication.similarity_threshold:
            return True
        
        # Content similarity (sample)
        content_sim = self._text_similarity(
            source1.content[:500],
            source2.content[:500]
        )
        if content_sim > self.config.deduplication.similarity_threshold:
            return True
        
        # Same URL domain
        if self._same_domain(source1.url, source2.url):
            # Check if content overlap is high
            if content_sim > 0.5:
                return True
        
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _same_domain(self, url1: str, url2: str) -> bool:
        """Check if URLs are from same domain"""
        try:
            from urllib.parse import urlparse
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False
    
    def _load_country_names(self) -> List[str]:
        """Load list of country names"""
        config = get_config()
        return config.monitored_countries + [
            # Add common variations
            "USA", "United States", "US",
            "UK", "United Kingdom", "Britain",
            "Russia", "Russian Federation",
            "South Korea", "Republic of Korea",
            "North Korea", "DPRK",
            "Iran", "Islamic Republic of Iran",
            "UAE", "United Arab Emirates",
        ]
    
    def _generate_entity_id(self, name: str, entity_type: EntityType) -> str:
        """Generate entity ID"""
        combined = f"{entity_type.value}|{name.lower()}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
