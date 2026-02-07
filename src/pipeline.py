"""
Main pipeline orchestrator: coordinates ingestion, normalization,
event extraction, scoring, and summarization.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import RawSource, Event, Assessment, Brief
from .ingestion import IngestionService
from .datasets import DatasetIngester
from .sanctions import SanctionsIngester
from .normalization import NormalizationPipeline
from .event_extraction import EventExtractor
from .scoring import ScoringEngine
from .summarization import SummarizationEngine
from .storage import Storage
from .config import get_config
from typing import List, Optional, Dict, Any


class IntelligencePipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.ingestion = IngestionService()
        self.dataset_ingester = DatasetIngester()
        self.sanctions_ingester = SanctionsIngester()
        self.normalization = NormalizationPipeline()
        self.event_extractor = EventExtractor()
        self.scoring_engine = ScoringEngine(self.storage)
        self.summarization_engine = SummarizationEngine(self.storage)
        self.config = get_config()
    
    def run_full_pipeline(self) -> Dict[str, any]:
        """Run the complete pipeline"""
        results = {
            'ingested': 0,
            'normalized': 0,
            'clusters': 0,
            'events': 0,
            'assessments': 0,
            'briefs': 0
        }
        
        # Step 1: Ingestion
        print("Step 1: Ingesting sources...")
        raw_sources = []
        
        # Fetch from news feeds and APIs
        news_sources = self.ingestion.fetch_all_sources()
        raw_sources.extend(news_sources)
        print(f"  Ingested {len(news_sources)} news sources")
        
        # Fetch from structured datasets
        try:
            dataset_sources = self.dataset_ingester.fetch_datasets()
            raw_sources.extend(dataset_sources)
            print(f"  Ingested {len(dataset_sources)} dataset sources")
        except Exception as e:
            print(f"  Error ingesting datasets: {e}")
        
        # Fetch sanctions lists
        try:
            sanctions_sources = self.sanctions_ingester.fetch_sanctions()
            raw_sources.extend(sanctions_sources)
            print(f"  Ingested {len(sanctions_sources)} sanctions sources")
        except Exception as e:
            print(f"  Error ingesting sanctions: {e}")
        
        results['ingested'] = len(raw_sources)
        print(f"  Total ingested: {len(raw_sources)} sources")
        
        # Save raw sources
        for source in raw_sources:
            self.storage.save_raw_source(source)
        
        # Step 2: Normalization
        print("Step 2: Normalizing sources...")
        normalized_sources = self.normalization.normalize(raw_sources)
        results['normalized'] = len(normalized_sources)
        print(f"  Normalized {len(normalized_sources)} sources")
        
        # Step 3: Clustering/Deduplication
        print("Step 3: Clustering and deduplicating...")
        clusters = self.normalization.cluster_sources(normalized_sources)
        results['clusters'] = len(clusters)
        print(f"  Created {len(clusters)} clusters")
        
        # Step 4: Event Extraction
        print("Step 4: Extracting events...")
        all_events = []
        for cluster in clusters:
            events = self.event_extractor.extract_events(cluster)
            all_events.extend(events)
            for event in events:
                self.storage.save_event(event)
        results['events'] = len(all_events)
        print(f"  Extracted {len(all_events)} events")
        
        # Step 5: Scoring
        print("Step 5: Calculating assessments...")
        assessments_created = 0
        for country in self.config.monitored_countries:
            # Get events for this country
            country_events = [e for e in all_events if country.lower() in e.location.lower()]
            
            if country_events or True:  # Create assessment even if no events (baseline)
                assessment = self.scoring_engine.calculate_assessment(country, country_events)
                self.storage.save_assessment(assessment)
                assessments_created += 1
        results['assessments'] = assessments_created
        print(f"  Created {assessments_created} assessments")
        
        # Step 6: Summarization
        print("Step 6: Generating briefs...")
        briefs_created = 0
        for country in self.config.monitored_countries[:5]:  # Limit for MVP demo
            brief = self.summarization_engine.generate_brief(country, "executive")
            self.storage.save_brief(brief)
            briefs_created += 1
        results['briefs'] = briefs_created
        print(f"  Generated {briefs_created} briefs")
        
        return results
    
    def get_assessment(self, target: str) -> Optional[Assessment]:
        """Get assessment for a target"""
        return self.storage.get_assessment(target)
    
    def get_brief(self, target: str, brief_type: str = "executive") -> Optional[Brief]:
        """Get brief for a target"""
        return self.summarization_engine.generate_brief(target, brief_type)
    
    def get_events(self, target: str, limit: int = 20) -> List[Event]:
        """Get events for a target"""
        return self.storage.get_events_by_location(target, limit=limit)
    
    def answer_query(self, target: str) -> Dict[str, any]:
        """
        Answer the core query: "What is happening in X region right now,
        why does it matter, how risky is it, and what evidence supports that assessment?"
        """
        assessment = self.get_assessment(target)
        events = self.get_events(target)
        brief = self.get_brief(target)
        
        return {
            'target': target,
            'assessment': assessment,
            'events': events,
            'brief': brief,
            'timestamp': datetime.utcnow().isoformat()
        }
