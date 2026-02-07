"""
Configuration management for the platform.
Loads and validates config.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ScoringConfig:
    """Scoring configuration"""
    weights: Dict[str, float]
    min_confidence: float
    baseline_days: int
    delta_periods: List[int]


@dataclass
class SourceConfig:
    """Source configuration"""
    tiers: Dict[str, Dict[str, Any]]
    feeds: List[Dict[str, Any]]


@dataclass
class DeduplicationConfig:
    """Deduplication configuration"""
    similarity_threshold: float
    max_sources_per_cluster: int
    time_window_hours: int


class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        with open(config_path, 'r') as f:
            self._raw = yaml.safe_load(f)
        
        # Load sub-configs
        self.scoring = ScoringConfig(
            weights=self._raw['scoring']['weights'],
            min_confidence=self._raw['scoring']['min_confidence'],
            baseline_days=self._raw['scoring']['baseline_days'],
            delta_periods=self._raw['scoring']['delta_periods']
        )
        
        self.sources = self._raw['sources']  # Keep as dict for flexibility
        
        self.deduplication = DeduplicationConfig(
            similarity_threshold=self._raw['deduplication']['similarity_threshold'],
            max_sources_per_cluster=self._raw['deduplication']['max_sources_per_cluster'],
            time_window_hours=self._raw['deduplication']['time_window_hours']
        )
        
        self.event_types = self._raw.get('event_types', {})
        self.monitored_countries = self._raw.get('monitored_countries', [])
        self.database = self._raw.get('database', {})
        self.api = self._raw.get('api', {})
    
    def get_source_tier_weight(self, tier: str) -> float:
        """Get weight for a source tier"""
        return self.sources.get('tiers', {}).get(tier, {}).get('weight', 0.5)
    
    def get_event_type_config(self, event_type: str) -> Dict[str, Any]:
        """Get configuration for an event type"""
        return self.event_types.get(event_type, {
            'severity_base': 0.5,
            'sub_score_weights': {}
        })


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
