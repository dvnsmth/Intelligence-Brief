"""
Tests for deduplication/clustering logic.
"""

import pytest
from datetime import datetime, timedelta

from src.models import RawSource, SourceTier
from src.normalization import NormalizationPipeline


def test_clustering_similar_sources():
    """Test that similar sources are clustered together"""
    pipeline = NormalizationPipeline()
    
    # Create similar sources
    base_time = datetime.utcnow()
    source1 = RawSource(
        source_id="1",
        url="https://example.com/news1",
        title="Major event in Country A",
        content="A significant event occurred in Country A today.",
        source_name="Test Source",
        tier=SourceTier.B,
        language="en",
        published_at=base_time,
        retrieved_at=base_time
    )
    
    source2 = RawSource(
        source_id="2",
        url="https://example.com/news2",
        title="Major event in Country A",
        content="A significant event occurred in Country A today.",
        source_name="Test Source",
        tier=SourceTier.B,
        language="en",
        published_at=base_time + timedelta(minutes=10),
        retrieved_at=base_time + timedelta(minutes=10)
    )
    
    source3 = RawSource(
        source_id="3",
        url="https://other.com/news",
        title="Completely different story",
        content="This is about something else entirely.",
        source_name="Other Source",
        tier=SourceTier.B,
        language="en",
        published_at=base_time,
        retrieved_at=base_time
    )
    
    clusters = pipeline.cluster_sources([source1, source2, source3])
    
    # Should have 2 clusters (similar sources grouped, different one separate)
    assert len(clusters) == 2
    
    # Similar sources should be in same cluster
    cluster_sizes = [len(c) for c in clusters]
    assert 2 in cluster_sizes  # One cluster should have 2 items


def test_clustering_time_window():
    """Test that sources outside time window are not clustered"""
    pipeline = NormalizationPipeline()
    
    base_time = datetime.utcnow()
    
    source1 = RawSource(
        source_id="1",
        url="https://example.com/news1",
        title="Same story",
        content="Same content",
        source_name="Test",
        tier=SourceTier.B,
        language="en",
        published_at=base_time,
        retrieved_at=base_time
    )
    
    # Source far in the future (outside time window)
    source2 = RawSource(
        source_id="2",
        url="https://example.com/news2",
        title="Same story",
        content="Same content",
        source_name="Test",
        tier=SourceTier.B,
        language="en",
        published_at=base_time + timedelta(days=2),  # Outside 24h window
        retrieved_at=base_time + timedelta(days=2)
    )
    
    clusters = pipeline.cluster_sources([source1, source2])
    
    # Should be separate clusters due to time window
    assert len(clusters) == 2
