"""
Tests for scoring engine.
"""

import pytest
from datetime import datetime, timedelta

from src.models import Event, EventType, SourceCitation, SourceTier, ConfidenceLevel
from src.scoring import ScoringEngine
from src.storage import Storage
from src.config import get_config


def test_sub_score_calculation():
    """Test that sub-scores are calculated correctly"""
    storage = Storage(":memory:")  # In-memory DB for testing
    engine = ScoringEngine(storage)
    
    # Create test events
    events = [
        Event(
            event_id="1",
            event_type=EventType.ARMED_CONFLICT,
            timestamp=datetime.utcnow(),
            location="Test Country",
            summary="Conflict event",
            sources=[],
            confidence=0.8,
            confidence_label=ConfidenceLevel.HIGH
        )
    ]
    
    assessment = engine.calculate_assessment("Test Country", events)
    
    # Should have sub-scores
    assert len(assessment.sub_scores) > 0
    
    # Security score should be affected by armed conflict
    security_score = assessment.get_sub_score('security')
    assert security_score is not None
    assert security_score.value < 70.0  # Should be below baseline due to conflict


def test_confidence_threshold():
    """Test that low-confidence events don't affect scores"""
    storage = Storage(":memory:")
    engine = ScoringEngine(storage)
    config = get_config()
    
    # Create low-confidence event
    events = [
        Event(
            event_id="1",
            event_type=EventType.ARMED_CONFLICT,
            timestamp=datetime.utcnow(),
            location="Test Country",
            summary="Low confidence event",
            sources=[],
            confidence=0.3,  # Below threshold
            confidence_label=ConfidenceLevel.LOW
        )
    ]
    
    assessment = engine.calculate_assessment("Test Country", events)
    
    # Score should be close to baseline (low confidence events filtered out)
    assert assessment.overall_score >= 65.0  # Should be near baseline
