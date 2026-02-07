"""
Event extraction: convert normalized content into structured events.
"""

import re
from datetime import datetime
from typing import List, Optional, Dict
import hashlib

from .models import (
    RawSource, Event, EventType, SourceCitation,
    ConfidenceLevel
)
from .config import get_config


class EventExtractor:
    """Extract structured events from normalized sources"""
    
    def __init__(self):
        self.config = get_config()
    
    def extract_events(self, source_cluster: List[RawSource]) -> List[Event]:
        """Extract events from a cluster of sources"""
        events = []
        
        # Use the first source as primary, others as corroboration
        primary_source = source_cluster[0]
        
        # Detect event type
        event_type = self._detect_event_type(primary_source)
        if not event_type:
            return []  # No recognizable event
        
        # Extract location
        location = self._extract_location(primary_source)
        if not location:
            return []  # Need location
        
        # Extract timestamp
        timestamp = primary_source.published_at or primary_source.retrieved_at
        
        # Build summary
        summary = self._build_summary(primary_source, event_type)
        
        # Calculate confidence based on source tier and corroboration
        confidence = self._calculate_confidence(source_cluster)
        
        # Build citations
        citations = [s.to_citation() for s in source_cluster[:self.config.deduplication.max_sources_per_cluster]]
        
        # Generate event ID
        event_id = self._generate_event_id(
            event_type, location, timestamp, primary_source.source_id
        )
        
        # Extract impact tags
        impact_tags = self._extract_impact_tags(primary_source, event_type)
        
        event = Event(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            location=location,
            summary=summary,
            sources=citations,
            confidence=confidence,
            impact_tags=impact_tags,
            evidence_links=[s.url for s in source_cluster]
        )
        
        event.update_confidence(confidence)
        
        return [event]
    
    def _detect_event_type(self, source: RawSource) -> Optional[EventType]:
        """Detect event type from source content"""
        text = f"{source.title} {source.content}".lower()
        
        # Pattern matching for event types
        patterns = {
            EventType.GOVERNMENT_CHANGE: [
                r'government.*change', r'leadership.*transition', r'new.*prime minister',
                r'president.*resign', r'coup', r'overthrow'
            ],
            EventType.ELECTION: [
                r'election', r'vote', r'ballot', r'referendum', r'polling'
            ],
            EventType.SANCTIONS: [
                r'sanction', r'embargo', r'trade ban', r'economic.*penalty'
            ],
            EventType.ARMED_CONFLICT: [
                r'armed conflict', r'war', r'battle', r'military.*attack',
                r'airstrike', r'bombing', r'combat'
            ],
            EventType.CEASEFIRE: [
                r'ceasefire', r'truce', r'peace.*agreement', r'armistice'
            ],
            EventType.TERRORIST_ATTACK: [
                r'terrorist.*attack', r'bombing', r'assassination', r'insurgent'
            ],
            EventType.CIVIL_UNREST: [
                r'protest', r'demonstration', r'riot', r'civil.*unrest',
                r'strike', r'uprising'
            ],
            EventType.BORDER_INCIDENT: [
                r'border.*incident', r'territorial.*dispute', r'border.*clash'
            ],
            EventType.TRADE_RESTRICTION: [
                r'trade.*restriction', r'tariff', r'import.*ban', r'export.*ban'
            ],
            EventType.ECONOMIC_CRISIS: [
                r'economic.*crisis', r'recession', r'inflation.*surge',
                r'currency.*collapse', r'default'
            ],
            EventType.INFRASTRUCTURE_DISRUPTION: [
                r'infrastructure.*disruption', r'pipeline.*attack', r'port.*closure',
                r'power.*outage', r'grid.*failure'
            ],
            EventType.NATURAL_DISASTER: [
                r'earthquake', r'flood', r'tsunami', r'natural.*disaster'
            ],
            EventType.DIPLOMATIC_RUPTURE: [
                r'diplomatic.*rupture', r'recall.*envoy', r'expel.*diplomat',
                r'break.*relations'
            ],
            EventType.MILITARY_MOBILIZATION: [
                r'military.*mobilization', r'troop.*movement', r'military.*exercise',
                r'deployment'
            ],
            EventType.CYBER_INCIDENT: [
                r'cyber.*attack', r'hack', r'data.*breach', r'cyber.*incident'
            ],
            EventType.LEGAL_CHANGE: [
                r'law.*change', r'regulation.*change', r'legal.*reform',
                r'constitutional.*change'
            ],
            EventType.STRATEGIC_INVESTMENT: [
                r'strategic.*investment', r'nationalization', r'state.*takeover'
            ]
        }
        
        for event_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return event_type
        
        return None
    
    def _extract_location(self, source: RawSource) -> Optional[str]:
        """Extract location from source"""
        text = f"{source.title} {source.content}"
        
        # Check monitored countries
        config = get_config()
        for country in config.monitored_countries:
            if country.lower() in text.lower():
                return country
        
        # Try to extract from title (often contains location)
        title_lower = source.title.lower()
        for country in config.monitored_countries:
            if country.lower() in title_lower:
                return country
        
        # Fallback: try common location patterns
        # This is basic - in production would use NER
        return None
    
    def _build_summary(self, source: RawSource, event_type: EventType) -> str:
        """Build factual summary from source"""
        # Use title as base, add key facts from content
        summary = source.title
        
        # Add first sentence of content if different
        content_sentences = source.content.split('.')
        if content_sentences and content_sentences[0].strip():
            first_sentence = content_sentences[0].strip()
            if first_sentence.lower() not in summary.lower():
                summary += f". {first_sentence}"
        
        return summary[:500]  # Limit length
    
    def _calculate_confidence(self, sources: List[RawSource]) -> float:
        """Calculate confidence based on source tiers and corroboration"""
        if not sources:
            return 0.0
        
        # Base confidence from primary source tier
        primary_tier = sources[0].tier
        tier_weights = {
            'A': 0.9,
            'B': 0.7,
            'C': 0.5,
            'D': 0.3
        }
        base_confidence = tier_weights.get(primary_tier.value, 0.5)
        
        # Boost for corroboration
        unique_sources = len(set(s.source_name for s in sources))
        if unique_sources >= 2:
            base_confidence = min(1.0, base_confidence + 0.1)
        if unique_sources >= 3:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Penalty if only Tier D sources
        if all(s.tier.value == 'D' for s in sources):
            base_confidence = min(base_confidence, 0.3)
        
        return base_confidence
    
    def _extract_impact_tags(self, source: RawSource, event_type: EventType) -> List[str]:
        """Extract impact tags"""
        tags = []
        text = source.content.lower()
        
        # Tag based on event type
        type_tags = {
            EventType.SANCTIONS: ['trade', 'economic'],
            EventType.TRADE_RESTRICTION: ['trade', 'economic'],
            EventType.ARMED_CONFLICT: ['security', 'infrastructure'],
            EventType.INFRASTRUCTURE_DISRUPTION: ['infrastructure', 'economic'],
            EventType.CYBER_INCIDENT: ['infrastructure', 'security'],
        }
        
        tags.extend(type_tags.get(event_type, []))
        
        # Add tags based on content keywords
        if any(word in text for word in ['trade', 'export', 'import']):
            tags.append('trade')
        if any(word in text for word in ['security', 'military', 'defense']):
            tags.append('security')
        if any(word in text for word in ['infrastructure', 'port', 'pipeline']):
            tags.append('infrastructure')
        
        return list(set(tags))  # Deduplicate
    
    def _generate_event_id(self, event_type: EventType, location: str,
                          timestamp: datetime, source_id: str) -> str:
        """Generate unique event ID"""
        combined = f"{event_type.value}|{location}|{timestamp.isoformat()}|{source_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
