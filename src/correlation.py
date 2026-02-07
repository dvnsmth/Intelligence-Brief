"""
Event correlation and pattern detection
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .models import Event, EventType
from .storage import Storage
from .config import get_config


class EventCorrelator:
    """Detect correlations and patterns in events"""
    
    def __init__(self, storage: Storage):
        self.storage = storage
    
    def find_correlated_events(self, event: Event, time_window_days: int = 30) -> List[Event]:
        """Find events correlated with a given event"""
        from datetime import datetime, timedelta
        
        correlated = []
        window_start = event.timestamp - timedelta(days=time_window_days)
        window_end = event.timestamp + timedelta(days=time_window_days)
        
        # Get events in time window
        all_events = self.storage.get_events_by_time_range(window_start, window_end)
        
        for other_event in all_events:
            if other_event.event_id == event.event_id:
                continue
            
            # Check for correlations
            correlation_score = self._calculate_correlation(event, other_event)
            if correlation_score > 0.5:
                correlated.append(other_event)
        
        return correlated
    
    def _calculate_correlation(self, event1: Event, event2: Event) -> float:
        """Calculate correlation score between two events"""
        score = 0.0
        
        # Same location increases correlation
        if event1.location.lower() == event2.location.lower():
            score += 0.3
        
        # Same event type increases correlation
        if event1.event_type == event2.event_type:
            score += 0.3
        
        # Temporal proximity
        time_diff = abs((event1.timestamp - event2.timestamp).total_seconds())
        if time_diff < 86400:  # Within 24 hours
            score += 0.2
        elif time_diff < 604800:  # Within 7 days
            score += 0.1
        
        # Shared entities (if implemented)
        shared_entities = set(event1.entities) & set(event2.entities)
        if shared_entities:
            score += 0.2
        
        return min(score, 1.0)
    
    def detect_patterns(self, events: List[Event]) -> List[Dict]:
        """Detect event patterns (escalation sequences, etc.)"""
        patterns = []
        
        # Group by location
        location_events: Dict[str, List[Event]] = defaultdict(list)
        for event in events:
            location_events[event.location].append(event)
        
        # Detect escalation patterns
        for location, loc_events in location_events.items():
            sorted_events = sorted(loc_events, key=lambda e: e.timestamp)
            
            # Check for escalation: civil_unrest -> armed_conflict
            for i in range(len(sorted_events) - 1):
                event1 = sorted_events[i]
                event2 = sorted_events[i + 1]
                
                if (event1.event_type == EventType.CIVIL_UNREST and 
                    event2.event_type == EventType.ARMED_CONFLICT):
                    time_diff = (event2.timestamp - event1.timestamp).days
                    if time_diff < 30:
                        patterns.append({
                            'type': 'escalation',
                            'location': location,
                            'sequence': ['civil_unrest', 'armed_conflict'],
                            'timeframe_days': time_diff,
                            'events': [event1.event_id, event2.event_id]
                        })
        
        return patterns
