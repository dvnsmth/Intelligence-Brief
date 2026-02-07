"""
Entity relationship mapping and resolution
"""

from typing import List, Dict, Set, Optional
from datetime import datetime
import hashlib

from .models import Entity, EntityType
from .storage import Storage


class EntityResolver:
    """Resolve and map entity relationships"""
    
    def __init__(self, storage: Storage):
        self.storage = storage
        self.entity_cache: Dict[str, Entity] = {}
    
    def extract_entities_from_text(self, text: str, location: str) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        # Extract country/region entities
        countries = self._extract_countries(text, location)
        for country in countries:
            entity_id = self._generate_entity_id(country, EntityType.COUNTRY)
            if entity_id not in self.entity_cache:
                entity = Entity(
                    entity_id=entity_id,
                    entity_type=EntityType.COUNTRY,
                    canonical_name=country,
                    geo_scope=country,
                    confidence=0.8
                )
                self.entity_cache[entity_id] = entity
            entities.append(self.entity_cache[entity_id])
        
        return entities
    
    def _extract_countries(self, text: str, location: str) -> Set[str]:
        """Extract country names from text"""
        from .config import get_config
        config = get_config()
        
        found = set()
        text_lower = text.lower()
        
        # Add location if it's a country
        for country in config.monitored_countries:
            if country.lower() in location.lower():
                found.add(country)
        
        # Search in text
        for country in config.monitored_countries:
            if country.lower() in text_lower:
                found.add(country)
        
        return found
    
    def _generate_entity_id(self, name: str, entity_type: EntityType) -> str:
        """Generate entity ID"""
        combined = f"{entity_type.value}|{name.lower()}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def build_relationships(self, events: List) -> List[Dict]:
        """Build entity relationships from events"""
        relationships = []
        
        # Group events by location to find regional patterns
        location_groups: Dict[str, List] = {}
        for event in events:
            location = event.location if hasattr(event, 'location') else ''
            if location not in location_groups:
                location_groups[location] = []
            location_groups[location].append(event)
        
        # Create relationships between countries with shared events
        locations = list(location_groups.keys())
        for i, loc1 in enumerate(locations):
            for loc2 in locations[i+1:]:
                # If both locations have similar event types, create relationship
                events1 = location_groups[loc1]
                events2 = location_groups[loc2]
                
                event_types1 = set(e.event_type.value if hasattr(e, 'event_type') else '' for e in events1)
                event_types2 = set(e.event_type.value if hasattr(e, 'event_type') else '' for e in events2)
                
                if event_types1 & event_types2:  # Common event types
                    relationship = {
                        'entity1': loc1,
                        'entity2': loc2,
                        'type': 'shared_events',
                        'strength': len(event_types1 & event_types2) / max(len(event_types1), len(event_types2), 1),
                        'common_events': list(event_types1 & event_types2)
                    }
                    relationships.append(relationship)
        
        return relationships
