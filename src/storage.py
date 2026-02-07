"""
Storage layer for raw sources, derived events, and assessments.
Uses SQLite for MVP with separate tables for each layer.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import (
    RawSource, Event, Entity, Assessment, Brief,
    SourceTier, EventType, EntityType, ConfidenceLevel,
    SourceCitation, SubScore
)
from .config import get_config


class Storage:
    """Storage manager for the intelligence platform"""
    
    def __init__(self, db_path: Optional[str] = None):
        config = get_config()
        if db_path is None:
            db_path = config.database.get('path', 'data/intelligence_brief.db')
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Raw sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_sources (
                    source_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    language TEXT NOT NULL,
                    published_at TEXT,
                    retrieved_at TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    location TEXT NOT NULL,
                    location_geo TEXT,
                    entities TEXT,
                    summary TEXT NOT NULL,
                    sources TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    confidence_label TEXT NOT NULL,
                    impact_tags TEXT,
                    evidence_links TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Entities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    canonical_name TEXT NOT NULL,
                    aliases TEXT,
                    geo_scope TEXT,
                    relationships TEXT,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    sub_scores TEXT NOT NULL,
                    delta_7d REAL NOT NULL,
                    delta_30d REAL NOT NULL,
                    delta_90d REAL NOT NULL,
                    drivers TEXT,
                    confidence REAL NOT NULL,
                    generated_at TEXT NOT NULL
                )
            """)
            
            # Briefs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS briefs (
                    brief_id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    what_changed TEXT NOT NULL,
                    why_it_matters TEXT NOT NULL,
                    what_to_watch TEXT NOT NULL,
                    citations TEXT NOT NULL,
                    confidence_markers TEXT,
                    generated_at TEXT NOT NULL,
                    brief_type TEXT NOT NULL
                )
            """)
            
            # Historical assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assessment_id TEXT NOT NULL,
                    target TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    sub_scores TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
                )
            """)
            
            # Entity relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entity_relationships (
                    relationship_id TEXT PRIMARY KEY,
                    entity1_id TEXT NOT NULL,
                    entity2_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Event correlations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_correlations (
                    correlation_id TEXT PRIMARY KEY,
                    event1_id TEXT NOT NULL,
                    event2_id TEXT NOT NULL,
                    correlation_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (event1_id) REFERENCES events(event_id),
                    FOREIGN KEY (event2_id) REFERENCES events(event_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(location)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_target ON assessments(target)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_sources_retrieved ON raw_sources(retrieved_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_assessments_target ON historical_assessments(target)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_assessments_date ON historical_assessments(generated_at)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_raw_source(self, source: RawSource):
        """Save raw source"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO raw_sources
                (source_id, url, title, content, source_name, tier, language,
                 published_at, retrieved_at, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.source_id,
                source.url,
                source.title,
                source.content,
                source.source_name,
                source.tier.value,
                source.language,
                source.published_at.isoformat() if source.published_at else None,
                source.retrieved_at.isoformat(),
                json.dumps(source.metadata),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_raw_source(self, source_id: str) -> Optional[RawSource]:
        """Get raw source by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM raw_sources WHERE source_id = ?", (source_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return RawSource(
                source_id=row['source_id'],
                url=row['url'],
                title=row['title'],
                content=row['content'],
                source_name=row['source_name'],
                tier=SourceTier(row['tier']),
                language=row['language'],
                published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else None,
                retrieved_at=datetime.fromisoformat(row['retrieved_at']),
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
    
    def save_event(self, event: Event):
        """Save event"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO events
                (event_id, event_type, timestamp, location, location_geo, entities,
                 summary, sources, confidence, confidence_label, impact_tags,
                 evidence_links, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.timestamp.isoformat(),
                event.location,
                event.location_geo,
                json.dumps(event.entities),
                event.summary,
                json.dumps([self._citation_to_dict(c) for c in event.sources]),
                event.confidence,
                event.confidence_label.value,
                json.dumps(event.impact_tags),
                json.dumps(event.evidence_links),
                event.created_at.isoformat(),
                event.updated_at.isoformat()
            ))
            conn.commit()
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get event by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_event(row)
    
    def get_events_by_location(self, location: str, limit: int = 100) -> List[Event]:
        """Get events for a location"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM events
                WHERE location LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{location}%", limit))
            return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def get_events_by_time_range(self, start: datetime, end: datetime) -> List[Event]:
        """Get events in time range"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM events
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
            """, (start.isoformat(), end.isoformat()))
            return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def save_assessment(self, assessment: Assessment):
        """Save assessment and historical record"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Save current assessment
            cursor.execute("""
                INSERT OR REPLACE INTO assessments
                (assessment_id, target, overall_score, sub_scores, delta_7d,
                 delta_30d, delta_90d, drivers, confidence, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment.assessment_id,
                assessment.target,
                assessment.overall_score,
                json.dumps([self._subscore_to_dict(s) for s in assessment.sub_scores]),
                assessment.delta_7d,
                assessment.delta_30d,
                assessment.delta_90d,
                json.dumps(assessment.drivers),
                assessment.confidence,
                assessment.generated_at.isoformat()
            ))
            
            # Save historical record
            cursor.execute("""
                INSERT INTO historical_assessments
                (assessment_id, target, overall_score, sub_scores, generated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                assessment.assessment_id,
                assessment.target,
                assessment.overall_score,
                json.dumps([self._subscore_to_dict(s) for s in assessment.sub_scores]),
                assessment.generated_at.isoformat()
            ))
            
            conn.commit()
    
    def get_historical_assessments(self, target: str, days: int = 90) -> List[Assessment]:
        """Get historical assessments for trend analysis"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM historical_assessments
                WHERE target = ? AND generated_at >= ?
                ORDER BY generated_at ASC
            """, (target, cutoff_date.isoformat()))
            
            rows = cursor.fetchall()
            assessments = []
            for row in rows:
                sub_scores_data = json.loads(row['sub_scores'])
                assessment = Assessment(
                    assessment_id=row['assessment_id'],
                    target=row['target'],
                    overall_score=row['overall_score'],
                    sub_scores=[self._dict_to_subscore(s) for s in sub_scores_data],
                    delta_7d=0.0,  # Will be calculated
                    delta_30d=0.0,
                    delta_90d=0.0,
                    drivers=[],
                    confidence=0.5,
                    generated_at=datetime.fromisoformat(row['generated_at'])
                )
                assessments.append(assessment)
            
            return assessments
    
    def get_assessment(self, target: str) -> Optional[Assessment]:
        """Get latest assessment for a target"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM assessments
                WHERE target = ?
                ORDER BY generated_at DESC
                LIMIT 1
            """, (target,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_assessment(row)
    
    def save_brief(self, brief: Brief):
        """Save brief"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO briefs
                (brief_id, target, what_changed, why_it_matters, what_to_watch,
                 citations, confidence_markers, generated_at, brief_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                brief.brief_id,
                brief.target,
                brief.what_changed,
                brief.why_it_matters,
                brief.what_to_watch,
                json.dumps([self._citation_to_dict(c) for c in brief.citations]),
                json.dumps({k: v.value for k, v in brief.confidence_markers.items()}),
                brief.generated_at.isoformat(),
                brief.brief_type
            ))
            conn.commit()
    
    def get_brief(self, target: str, brief_type: str = "executive") -> Optional[Brief]:
        """Get latest brief for a target"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM briefs
                WHERE target = ? AND brief_type = ?
                ORDER BY generated_at DESC
                LIMIT 1
            """, (target, brief_type))
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_brief(row)
    
    # Helper methods for serialization
    def _citation_to_dict(self, citation: SourceCitation) -> Dict[str, Any]:
        """Convert citation to dict"""
        return {
            'url': citation.url,
            'title': citation.title,
            'source_name': citation.source_name,
            'tier': citation.tier.value,
            'published_at': citation.published_at.isoformat() if citation.published_at else None,
            'retrieved_at': citation.retrieved_at.isoformat() if citation.retrieved_at else None
        }
    
    def _dict_to_citation(self, d: Dict[str, Any]) -> SourceCitation:
        """Convert dict to citation"""
        return SourceCitation(
            url=d['url'],
            title=d['title'],
            source_name=d['source_name'],
            tier=SourceTier(d['tier']),
            published_at=datetime.fromisoformat(d['published_at']) if d.get('published_at') else None,
            retrieved_at=datetime.fromisoformat(d['retrieved_at']) if d.get('retrieved_at') else None
        )
    
    def _subscore_to_dict(self, score: SubScore) -> Dict[str, Any]:
        """Convert subscore to dict"""
        return {
            'name': score.name,
            'value': score.value,
            'delta_7d': score.delta_7d,
            'delta_30d': score.delta_30d,
            'delta_90d': score.delta_90d,
            'drivers': score.drivers
        }
    
    def _dict_to_subscore(self, d: Dict[str, Any]) -> SubScore:
        """Convert dict to subscore"""
        return SubScore(
            name=d['name'],
            value=d['value'],
            delta_7d=d.get('delta_7d', 0.0),
            delta_30d=d.get('delta_30d', 0.0),
            delta_90d=d.get('delta_90d', 0.0),
            drivers=d.get('drivers', [])
        )
    
    def _row_to_event(self, row) -> Event:
        """Convert database row to Event"""
        sources_data = json.loads(row['sources'])
        return Event(
            event_id=row['event_id'],
            event_type=EventType(row['event_type']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            location=row['location'],
            summary=row['summary'],
            location_geo=row['location_geo'],
            entities=json.loads(row['entities']) if row['entities'] else [],
            sources=[self._dict_to_citation(s) for s in sources_data],
            confidence=row['confidence'],
            confidence_label=ConfidenceLevel(row['confidence_label']),
            impact_tags=json.loads(row['impact_tags']) if row['impact_tags'] else [],
            evidence_links=json.loads(row['evidence_links']) if row['evidence_links'] else [],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    def _row_to_assessment(self, row) -> Assessment:
        """Convert database row to Assessment"""
        sub_scores_data = json.loads(row['sub_scores'])
        return Assessment(
            assessment_id=row['assessment_id'],
            target=row['target'],
            overall_score=row['overall_score'],
            sub_scores=[self._dict_to_subscore(s) for s in sub_scores_data],
            delta_7d=row['delta_7d'],
            delta_30d=row['delta_30d'],
            delta_90d=row['delta_90d'],
            drivers=json.loads(row['drivers']) if row['drivers'] else [],
            confidence=row['confidence'],
            generated_at=datetime.fromisoformat(row['generated_at'])
        )
    
    def _row_to_brief(self, row) -> Brief:
        """Convert database row to Brief"""
        citations_data = json.loads(row['citations'])
        confidence_markers_data = json.loads(row['confidence_markers']) if row['confidence_markers'] else {}
        return Brief(
            brief_id=row['brief_id'],
            target=row['target'],
            what_changed=row['what_changed'],
            why_it_matters=row['why_it_matters'],
            what_to_watch=row['what_to_watch'],
            citations=[self._dict_to_citation(c) for c in citations_data],
            confidence_markers={k: ConfidenceLevel(v) for k, v in confidence_markers_data.items()},
            generated_at=datetime.fromisoformat(row['generated_at']),
            brief_type=row['brief_type']
        )
