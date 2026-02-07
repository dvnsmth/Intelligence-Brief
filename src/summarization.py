"""
Summarization module: generate situation briefs with fact/assessment separation.
"""

from datetime import datetime
from typing import List, Dict

from .models import Brief, Event, Assessment, SourceCitation, ConfidenceLevel
from .storage import Storage


class SummarizationEngine:
    """Generate situation briefs"""
    
    def __init__(self, storage: Storage):
        self.storage = storage
    
    def generate_brief(self, target: str, brief_type: str = "executive") -> Brief:
        """Generate brief for a target"""
        # Get assessment
        assessment = self.storage.get_assessment(target)
        if not assessment:
            # Create empty brief if no assessment
            return self._create_empty_brief(target, brief_type)
        
        # Get recent events
        events = self.storage.get_events_by_location(target, limit=10)
        
        # Generate sections
        what_changed = self._generate_what_changed(events, brief_type)
        why_it_matters = self._generate_why_it_matters(assessment, events, brief_type)
        what_to_watch = self._generate_what_to_watch(assessment, events, brief_type)
        
        # Collect citations
        citations = self._collect_citations(events)
        
        # Generate confidence markers
        confidence_markers = self._generate_confidence_markers(events, assessment)
        
        brief = Brief(
            brief_id=f"brief_{target}_{datetime.utcnow().isoformat()}",
            target=target,
            what_changed=what_changed,
            why_it_matters=why_it_matters,
            what_to_watch=what_to_watch,
            citations=citations,
            confidence_markers=confidence_markers,
            brief_type=brief_type
        )
        
        return brief
    
    def _generate_what_changed(self, events: List[Event], brief_type: str) -> str:
        """Generate factual 'what changed' section"""
        if not events:
            return "No significant events reported in the recent period."
        
        # Sort by timestamp (most recent first)
        sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        # Take top 3-5 events
        top_events = sorted_events[:5 if brief_type == "analyst" else 3]
        
        facts = []
        for event in top_events:
            fact = f"On {event.timestamp.strftime('%Y-%m-%d')}, {event.summary}"
            
            # Add location if not obvious
            if event.location:
                fact += f" (Location: {event.location})"
            
            # Add confidence
            fact += f" [Confidence: {event.confidence_label.value}]"
            
            # Add source count
            source_count = len(event.sources)
            fact += f" (Sources: {source_count})"
            
            facts.append(fact)
        
        return ". ".join(facts) + "."
    
    def _generate_why_it_matters(self, assessment: Assessment, events: List[Event],
                                 brief_type: str) -> str:
        """Generate assessment 'why it matters' section with historical context"""
        # Get historical context
        historical_assessments = self.storage.get_historical_assessments(assessment.target, days=90)
        
        # Analyze score changes
        deltas = {
            '7d': assessment.delta_7d,
            '30d': assessment.delta_30d,
            '90d': assessment.delta_90d
        }
        
        # Determine trend with more nuance
        trend_desc = "stable"
        trend_strength = "moderate"
        if deltas['7d'] < -10:
            trend_desc = "declining"
            trend_strength = "significant"
        elif deltas['7d'] < -5:
            trend_desc = "declining"
        elif deltas['7d'] > 10:
            trend_desc = "improving"
            trend_strength = "significant"
        elif deltas['7d'] > 5:
            trend_desc = "improving"
        
        # Historical comparison
        historical_context = ""
        if historical_assessments and len(historical_assessments) > 1:
            oldest_score = historical_assessments[0].overall_score
            if abs(assessment.overall_score - oldest_score) > 10:
                if assessment.overall_score < oldest_score:
                    historical_context = f"Score has declined {oldest_score - assessment.overall_score:.1f} points over the past 90 days. "
                else:
                    historical_context = f"Score has improved {assessment.overall_score - oldest_score:.1f} points over the past 90 days. "
        
        # Get key sub-scores with context
        key_scores = []
        for sub_score in assessment.sub_scores:
            if abs(sub_score.delta_7d) > 3:
                trend_indicator = "declining" if sub_score.delta_7d < 0 else "improving"
                key_scores.append(f"{sub_score.name} ({sub_score.value:.1f}, {trend_indicator} Δ{sub_score.delta_7d:+.1f})")
        
        assessment_text = f"Overall stability score: {assessment.overall_score:.1f}/100 "
        assessment_text += f"(trend: {trend_strength} {trend_desc}). "
        
        if historical_context:
            assessment_text += historical_context
        
        if key_scores:
            assessment_text += f"Notable changes in: {', '.join(key_scores[:3])}. "
        
        # Add regional implications if significant events
        if events:
            high_impact_events = [e for e in events if e.confidence > 0.7 and e.event_type in [
                'armed_conflict', 'sanctions', 'government_change'
            ]]
            if high_impact_events:
                assessment_text += f"Recent high-impact events ({len(high_impact_events)}) suggest ongoing volatility. "
        
        # Add likelihood language (not predictions)
        if assessment.overall_score < 50:
            assessment_text += "Current conditions suggest elevated risk levels requiring close monitoring. "
        elif assessment.overall_score > 80:
            assessment_text += "Current conditions indicate relative stability, though continued monitoring is advised. "
        
        return assessment_text
    
    def _generate_what_to_watch(self, assessment: Assessment, events: List[Event],
                                brief_type: str) -> str:
        """Generate 'what to watch' section with scenarios and indicators"""
        watch_items = []
        
        # Key drivers
        if assessment.drivers:
            watch_items.append(f"Monitor developments related to recent events "
                            f"that are driving score changes.")
        
        # Low-scoring dimensions
        for sub_score in assessment.sub_scores:
            if sub_score.value < 60:
                watch_items.append(f"Watch for changes in {sub_score.name} indicators "
                                 f"(current: {sub_score.value:.1f}/100).")
        
        # Event types to watch
        event_types = set(e.event_type for e in events)
        if len(event_types) > 0:
            watch_items.append(f"Continue monitoring for: "
                             f"{', '.join([e.value.replace('_', ' ') for e in event_types[:3]])}.")
        
        if not watch_items:
            watch_items.append("Continue standard monitoring protocols.")
        
        return " ".join(watch_items)
    
    def _collect_citations(self, events: List[Event]) -> List[SourceCitation]:
        """Collect unique citations from events"""
        citations_dict = {}
        
        for event in events:
            for citation in event.sources:
                # Use URL as key to deduplicate
                if citation.url not in citations_dict:
                    citations_dict[citation.url] = citation
        
        return list(citations_dict.values())[:10]  # Limit to 10
    
    def _generate_confidence_markers(self, events: List[Event],
                                    assessment: Assessment) -> Dict[str, ConfidenceLevel]:
        """Generate confidence markers for key claims"""
        markers = {}
        
        # Overall assessment confidence
        if assessment.confidence >= 0.7:
            markers['overall_assessment'] = ConfidenceLevel.HIGH
        elif assessment.confidence >= 0.4:
            markers['overall_assessment'] = ConfidenceLevel.MEDIUM
        else:
            markers['overall_assessment'] = ConfidenceLevel.LOW
        
        # Event confidence (average)
        if events:
            avg_event_confidence = sum(e.confidence for e in events) / len(events)
            if avg_event_confidence >= 0.7:
                markers['events'] = ConfidenceLevel.HIGH
            elif avg_event_confidence >= 0.4:
                markers['events'] = ConfidenceLevel.MEDIUM
            else:
                markers['events'] = ConfidenceLevel.LOW
        
        return markers
    
    def _create_empty_brief(self, target: str, brief_type: str) -> Brief:
        """Create empty brief when no data available"""
        return Brief(
            brief_id=f"brief_{target}_{datetime.utcnow().isoformat()}",
            target=target,
            what_changed="No data available for this region at this time.",
            why_it_matters="Insufficient data to assess current conditions.",
            what_to_watch="Continue monitoring for new information.",
            citations=[],
            confidence_markers={'overall_assessment': ConfidenceLevel.LOW},
            brief_type=brief_type
        )
