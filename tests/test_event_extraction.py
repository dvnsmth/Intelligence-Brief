"""
Tests for event extraction.
"""

import pytest
from datetime import datetime

from src.models import RawSource, SourceTier, EventType
from src.event_extraction import EventExtractor


def test_event_type_detection():
    """Test that event types are correctly detected"""
    extractor = EventExtractor()
    
    # Test armed conflict detection
    source = RawSource(
        source_id="1",
        url="https://example.com/news",
        title="Military conflict escalates in Region X",
        content="Armed forces engaged in battle today. Airstrikes reported.",
        source_name="Test",
        tier=SourceTier.B,
        language="en",
        published_at=datetime.utcnow(),
        retrieved_at=datetime.utcnow()
    )
    
    event_type = extractor._detect_event_type(source)
    assert event_type == EventType.ARMED_CONFLICT
    
    # Test sanctions detection
    source2 = RawSource(
        source_id="2",
        url="https://example.com/news2",
        title="New sanctions imposed",
        content="Economic sanctions were announced today.",
        source_name="Test",
        tier=SourceTier.B,
        language="en",
        published_at=datetime.utcnow(),
        retrieved_at=datetime.utcnow()
    )
    
    event_type2 = extractor._detect_event_type(source2)
    assert event_type2 == EventType.SANCTIONS


def test_confidence_calculation():
    """Test confidence calculation"""
    extractor = EventExtractor()
    
    # Single Tier B source
    sources1 = [
        RawSource(
            source_id="1",
            url="https://example.com/news",
            title="Test",
            content="Test content",
            source_name="Source1",
            tier=SourceTier.B,
            language="en",
            published_at=datetime.utcnow(),
            retrieved_at=datetime.utcnow()
        )
    ]
    
    confidence1 = extractor._calculate_confidence(sources1)
    assert 0.6 <= confidence1 <= 0.8  # Tier B should be around 0.7
    
    # Multiple sources (corroboration)
    sources2 = sources1 + [
        RawSource(
            source_id="2",
            url="https://other.com/news",
            title="Test",
            content="Test content",
            source_name="Source2",
            tier=SourceTier.B,
            language="en",
            published_at=datetime.utcnow(),
            retrieved_at=datetime.utcnow()
        )
    ]
    
    confidence2 = extractor._calculate_confidence(sources2)
    assert confidence2 > confidence1  # Should be higher with corroboration
