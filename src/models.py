"""
Data models for the intelligence platform.
Defines schemas for RawSource, Event, Entity, and Assessment.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SourceTier(str, Enum):
    """Source credibility tiers"""
    A = "A"  # Official sources, verified datasets
    B = "B"  # Tier-1 media, reputable NGOs
    C = "C"  # Regional outlets with known reliability
    D = "D"  # Social or unverified


class EventType(str, Enum):
    """Event taxonomy v0.1"""
    GOVERNMENT_CHANGE = "government_change"
    ELECTION = "election"
    SANCTIONS = "sanctions"
    ARMED_CONFLICT = "armed_conflict"
    CEASEFIRE = "ceasefire"
    TERRORIST_ATTACK = "terrorist_attack"
    CIVIL_UNREST = "civil_unrest"
    BORDER_INCIDENT = "border_incident"
    TRADE_RESTRICTION = "trade_restriction"
    ECONOMIC_CRISIS = "economic_crisis"
    INFRASTRUCTURE_DISRUPTION = "infrastructure_disruption"
    NATURAL_DISASTER = "natural_disaster"
    DIPLOMATIC_RUPTURE = "diplomatic_rupture"
    MILITARY_MOBILIZATION = "military_mobilization"
    CYBER_INCIDENT = "cyber_incident"
    LEGAL_CHANGE = "legal_change"
    STRATEGIC_INVESTMENT = "strategic_investment"


class EntityType(str, Enum):
    """Entity types"""
    COUNTRY = "country"
    REGION = "region"
    CITY = "city"
    LEADER = "leader"
    GOVERNMENT_AGENCY = "government_agency"
    ARMED_GROUP = "armed_group"
    CORPORATION = "corporation"
    INFRASTRUCTURE = "infrastructure"
    INTERNATIONAL_ORG = "international_org"


class ConfidenceLevel(str, Enum):
    """Confidence levels"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class SourceCitation:
    """Citation for a source"""
    url: str
    title: str
    source_name: str
    tier: SourceTier
    published_at: Optional[datetime] = None
    retrieved_at: Optional[datetime] = None


@dataclass
class RawSource:
    """Raw ingested source material"""
    source_id: str
    url: str
    title: str
    content: str
    source_name: str
    tier: SourceTier
    language: str
    published_at: Optional[datetime]
    retrieved_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_citation(self) -> SourceCitation:
        """Convert to citation format"""
        return SourceCitation(
            url=self.url,
            title=self.title,
            source_name=self.source_name,
            tier=self.tier,
            published_at=self.published_at,
            retrieved_at=self.retrieved_at
        )


@dataclass
class Entity:
    """Canonical entity representation"""
    entity_id: str
    entity_type: EntityType
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    geo_scope: Optional[str] = None  # Country code or region
    relationships: Dict[str, str] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class Event:
    """Canonical event representation"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    location: str  # Location name
    summary: str  # Factual summary
    location_geo: Optional[str] = None  # Geo coordinates or country code
    entities: List[str] = field(default_factory=list)  # Entity IDs
    sources: List[SourceCitation] = field(default_factory=list)
    confidence: float = 0.5  # 0.0 to 1.0
    confidence_label: ConfidenceLevel = ConfidenceLevel.MEDIUM
    impact_tags: List[str] = field(default_factory=list)  # e.g., ["trade", "security"]
    evidence_links: List[str] = field(default_factory=list)  # Links to raw sources
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_confidence(self, new_confidence: float):
        """Update confidence and label"""
        self.confidence = max(0.0, min(1.0, new_confidence))
        if self.confidence >= 0.7:
            self.confidence_label = ConfidenceLevel.HIGH
        elif self.confidence >= 0.4:
            self.confidence_label = ConfidenceLevel.MEDIUM
        else:
            self.confidence_label = ConfidenceLevel.LOW
        self.updated_at = datetime.utcnow()


@dataclass
class SubScore:
    """Sub-score for a specific dimension"""
    name: str  # e.g., "political", "security"
    value: float  # 0-100 (higher = more stable)
    delta_7d: float = 0.0
    delta_30d: float = 0.0
    delta_90d: float = 0.0
    drivers: List[str] = field(default_factory=list)  # Event IDs contributing


@dataclass
class Assessment:
    """Risk and stability assessment for a country/region"""
    assessment_id: str
    target: str  # Country or region name
    overall_score: float  # 0-100 (higher = more stable)
    sub_scores: List[SubScore] = field(default_factory=list)
    delta_7d: float = 0.0
    delta_30d: float = 0.0
    delta_90d: float = 0.0
    drivers: List[str] = field(default_factory=list)  # Top event IDs
    confidence: float = 0.5
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_sub_score(self, name: str) -> Optional[SubScore]:
        """Get sub-score by name"""
        for score in self.sub_scores:
            if score.name == name:
                return score
        return None


@dataclass
class Brief:
    """Situation brief"""
    brief_id: str
    target: str  # Country or region
    what_changed: str  # Facts section
    why_it_matters: str  # Assessment section
    what_to_watch: str  # Scenarios and indicators
    citations: List[SourceCitation] = field(default_factory=list)
    confidence_markers: Dict[str, ConfidenceLevel] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    brief_type: str = "executive"  # "executive" or "analyst"
