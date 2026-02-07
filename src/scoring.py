"""
Scoring engine: calculate risk and stability scores from events.
Uses transparent, rule-based approach with configurable weights.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .models import Event, Assessment, SubScore, EventType
from .config import get_config
from .storage import Storage


class ScoringEngine:
    """Calculate risk and stability scores"""
    
    def __init__(self, storage: Storage):
        self.storage = storage
        self.config = get_config()
    
    def calculate_assessment(self, target: str, events: Optional[List[Event]] = None) -> Assessment:
        """Calculate assessment for a target country/region"""
        if events is None:
            # Get events for this target
            events = self.storage.get_events_by_location(target)
        
        # Filter events by confidence threshold
        valid_events = [
            e for e in events
            if e.confidence >= self.config.scoring.min_confidence
        ]
        
        # Calculate sub-scores
        sub_scores = self._calculate_sub_scores(target, valid_events)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(sub_scores)
        
        # Calculate deltas
        deltas = self._calculate_deltas(target, overall_score)
        
        # Get top drivers
        drivers = self._get_top_drivers(valid_events)
        
        # Calculate confidence
        confidence = self._calculate_assessment_confidence(valid_events)
        
        assessment = Assessment(
            assessment_id=f"assess_{target}_{datetime.utcnow().isoformat()}",
            target=target,
            overall_score=overall_score,
            sub_scores=sub_scores,
            delta_7d=deltas['7d'],
            delta_30d=deltas['30d'],
            delta_90d=deltas['90d'],
            drivers=drivers,
            confidence=confidence
        )
        
        return assessment
    
    def _calculate_sub_scores(self, target: str, events: List[Event]) -> List[SubScore]:
        """Calculate sub-scores for each dimension"""
        sub_score_names = list(self.config.scoring.weights.keys())
        sub_scores = []
        
        for name in sub_score_names:
            # Start with baseline (assume stability = 70/100)
            baseline = 70.0
            
            # Calculate impact from events
            impact = self._calculate_dimension_impact(name, events)
            
            # Apply impact (negative impact reduces stability)
            score_value = max(0.0, min(100.0, baseline - impact))
            
            # Calculate deltas
            deltas = self._calculate_sub_score_deltas(target, name, score_value)
            
            # Get drivers for this dimension
            drivers = self._get_dimension_drivers(name, events)
            
            sub_score = SubScore(
                name=name,
                value=score_value,
                delta_7d=deltas['7d'],
                delta_30d=deltas['30d'],
                delta_90d=deltas['90d'],
                drivers=drivers
            )
            sub_scores.append(sub_score)
        
        return sub_scores
    
    def _calculate_dimension_impact(self, dimension: str, events: List[Event]) -> float:
        """Calculate impact on a specific dimension"""
        total_impact = 0.0
        
        for event in events:
            # Get event type config
            event_config = self.config.get_event_type_config(event.event_type.value)
            severity = event_config.get('severity_base', 0.5)
            
            # Get dimension weight for this event type
            sub_score_weights = event_config.get('sub_score_weights', {})
            dimension_weight = sub_score_weights.get(dimension, 0.0)
            
            if dimension_weight == 0.0:
                continue
            
            # Calculate impact: severity * dimension_weight * confidence
            impact = severity * dimension_weight * event.confidence * 20.0  # Scale to 0-20
            
            total_impact += impact
        
        return total_impact
    
    def _calculate_overall_score(self, sub_scores: List[SubScore]) -> float:
        """Calculate overall score from sub-scores"""
        total = 0.0
        total_weight = 0.0
        
        for sub_score in sub_scores:
            weight = self.config.scoring.weights.get(sub_score.name, 0.0)
            total += sub_score.value * weight
            total_weight += weight
        
        if total_weight == 0:
            return 70.0  # Baseline
        
        return total / total_weight
    
    def _calculate_deltas(self, target: str, current_score: float) -> Dict[str, float]:
        """Calculate score deltas vs historical baseline"""
        from datetime import datetime, timedelta
        
        # Get historical assessments
        historical_assessments = self.storage.get_historical_assessments(target, days=90)
        
        if not historical_assessments:
            return {'7d': 0.0, '30d': 0.0, '90d': 0.0}
        
        # Find scores at specific time points
        now = datetime.utcnow()
        date_7d = now - timedelta(days=7)
        date_30d = now - timedelta(days=30)
        date_90d = now - timedelta(days=90)
        
        def find_closest_score(target_date):
            closest = None
            min_diff = float('inf')
            for assessment in historical_assessments:
                diff = abs((assessment.generated_at - target_date).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest = assessment
            return closest.overall_score if closest else current_score
        
        score_7d = find_closest_score(date_7d)
        score_30d = find_closest_score(date_30d)
        score_90d = find_closest_score(date_90d)
        
        deltas = {
            '7d': current_score - score_7d,
            '30d': current_score - score_30d,
            '90d': current_score - score_90d
        }
        
        return deltas
    
    def _calculate_sub_score_deltas(self, target: str, dimension: str,
                                    current_value: float) -> Dict[str, float]:
        """Calculate sub-score deltas from historical data"""
        from datetime import datetime, timedelta
        
        historical_assessments = self.storage.get_historical_assessments(target, days=90)
        
        if not historical_assessments:
            return {'7d': 0.0, '30d': 0.0, '90d': 0.0}
        
        now = datetime.utcnow()
        date_7d = now - timedelta(days=7)
        date_30d = now - timedelta(days=30)
        date_90d = now - timedelta(days=90)
        
        def find_closest_sub_score(target_date):
            closest = None
            min_diff = float('inf')
            for assessment in historical_assessments:
                diff = abs((assessment.generated_at - target_date).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest = assessment
            if closest:
                sub_score = closest.get_sub_score(dimension)
                return sub_score.value if sub_score else current_value
            return current_value
        
        value_7d = find_closest_sub_score(date_7d)
        value_30d = find_closest_sub_score(date_30d)
        value_90d = find_closest_sub_score(date_90d)
        
        return {
            '7d': current_value - value_7d,
            '30d': current_value - value_30d,
            '90d': current_value - value_90d
        }
    
    def _get_top_drivers(self, events: List[Event], limit: int = 5) -> List[str]:
        """Get top event IDs driving score changes"""
        # Sort by impact (severity * confidence)
        scored_events = []
        for event in events:
            event_config = self.config.get_event_type_config(event.event_type.value)
            severity = event_config.get('severity_base', 0.5)
            impact_score = severity * event.confidence
            scored_events.append((impact_score, event.event_id))
        
        scored_events.sort(reverse=True)
        return [event_id for _, event_id in scored_events[:limit]]
    
    def _get_dimension_drivers(self, dimension: str, events: List[Event],
                               limit: int = 3) -> List[str]:
        """Get top event IDs for a specific dimension"""
        scored_events = []
        
        for event in events:
            event_config = self.config.get_event_type_config(event.event_type.value)
            sub_score_weights = event_config.get('sub_score_weights', {})
            dimension_weight = sub_score_weights.get(dimension, 0.0)
            
            if dimension_weight == 0.0:
                continue
            
            severity = event_config.get('severity_base', 0.5)
            impact_score = severity * dimension_weight * event.confidence
            scored_events.append((impact_score, event.event_id))
        
        scored_events.sort(reverse=True)
        return [event_id for _, event_id in scored_events[:limit]]
    
    def _calculate_assessment_confidence(self, events: List[Event]) -> float:
        """Calculate overall confidence for assessment"""
        if not events:
            return 0.3  # Low confidence with no events
        
        # Average confidence of contributing events
        avg_confidence = sum(e.confidence for e in events) / len(events)
        
        # Boost for multiple events
        if len(events) >= 5:
            avg_confidence = min(1.0, avg_confidence + 0.1)
        
        return avg_confidence
