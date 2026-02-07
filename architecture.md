# Architecture Overview

## 1. System Goals
- Continuous ingestion of global signals
- Transparent sourcing and confidence labeling
- Explainable risk scoring with configurable weights
- Separation of raw data, derived facts, and assessments
- Extensible pipeline for new sources and event types

## 2. High-Level Architecture

**Core components**
- Ingestion service
- Language detection and translation
- Entity recognition and resolution
- Story clustering and deduplication
- Event extraction and enrichment
- Confidence scoring
- Storage layers (raw, derived, assessments)
- Summarization and brief generation
- Scoring engine
- Alerting and delivery
- UI and API

## 3. Data Flow (Textual Diagram)
1. Sources -> Ingestion -> Raw Store
2. Raw Store -> Language Detection / Translation
3. Translated Text -> Entity Recognition / Resolution
4. Entities + Text -> Story Clustering / Deduplication
5. Clusters -> Event Extraction
6. Events -> Confidence Scoring
7. Events + Confidence -> Derived Store
8. Derived Store -> Scoring Engine -> Assessment Store
9. Assessment Store -> Summarization -> Briefs
10. Score Changes -> Alerting -> Delivery

## 4. Pipeline Stage Responsibilities

### 4.1 Ingestion
- Fetch documents and metadata
- Store raw text with provenance
- Track update times and source reliability

### 4.2 Language Detection and Translation
- Detect language
- Translate to English for analysis
- Retain original language for traceability

### 4.3 Entity Recognition and Resolution
- Identify entities (countries, leaders, orgs)
- Map to canonical IDs
- Record aliases and ambiguities

### 4.4 Story Clustering and Deduplication
- Group semantically similar items
- Detect shared upstream sources
- Prevent narrative amplification

### 4.5 Event Extraction
- Identify event type, time, location, actors
- Attach supporting evidence excerpts

### 4.6 Confidence Scoring
- Weight by source credibility
- Increase confidence with corroboration
- Decrease with contradictions

### 4.7 Storage
- Raw store: original text and metadata
- Derived store: extracted events and entities
- Assessment store: scores, briefs, and rationale

## 5. Data Model (Core)

### 5.1 Event (canonical)
- event_id
- event_type
- timestamp
- location (name + geo)
- entities (canonical IDs)
- summary (factual)
- sources (URLs + provenance)
- confidence (numeric + label)
- impact_tags
- evidence_links
- created_at / updated_at

### 5.2 Entity (canonical)
- entity_id
- entity_type
- canonical_name
- aliases
- geo_scope
- relationships (optional)
- confidence

### 5.3 Assessment
- assessment_id
- target (country/region)
- overall_score
- sub_scores
- deltas (7/30/90 day)
- drivers (top events)
- confidence
- generated_at

## 6. Event Taxonomy v0.1
- Government change / leadership transition
- Election / referendum
- Sanctions imposed / lifted
- Armed conflict escalation
- Ceasefire or peace agreement
- Terrorist attack / insurgent incident
- Civil unrest / protest wave
- Border incident / territorial dispute
- Trade restriction / tariff change
- Economic crisis indicator (default, inflation shock)
- Infrastructure disruption (port, pipeline, grid)
- Natural disaster (geopolitically relevant)
- Diplomatic rupture / recall of envoy
- Military mobilization / exercises
- Cyber incident affecting critical infrastructure
- Major legal / regulatory change
- Strategic investment / nationalization

## 7. Scoring Framework (Explainable)

**Conceptual formula**
OverallScore = sum(w_i * S_i * C_i)

**Sub-scores**
- Political
- Security
- Economic
- Social
- Governance
- External

**Confidence handling**
- Low confidence reduces impact
- Confidence < 0.4 does not affect score (watchlist only)

**Configuration**
- Weights stored in versioned config
- Changeable without redeploy
- Historical scoring retained for backtesting

## 8. Summarization Rules
- Separate facts and assessments
- Likelihood bands instead of predictions
- Non-alarmist, neutral tone
- Cite every factual claim
- Avoid causal claims without evidence

## 9. Guardrails and Controls
- Deduplication prevents source flooding
- Unique-source limits per event
- Tier D sources cannot confirm alone
- Contradictory evidence lowers confidence
- Avoid over-precision in forecasts

## 10. Non-Functional Requirements
- **Traceability:** every claim maps to evidence
- **Auditability:** versioned scores and weights
- **Scalability:** support hourly ingestion bursts
- **Reliability:** graceful degradation when sources fail
- **Security:** access control and data isolation

## 11. MVP Scope (Architecture View)
- Tier A/B sources only
- 10 core event types
- Scorecards + briefs for top 30 countries
- Dashboard + email alerts

## 12. Open Architecture Decisions
- Real-time streaming vs batch processing
- Multi-tenant SaaS vs single-tenant deployments
- Storage stack selection (document vs graph hybrid)
- Translation provider choice

## 13. Acceptance Criteria for Architecture
- Pipeline produces traceable events with confidence
- Deduplication reduces duplicate events by >=80 percent
- Scorecards reflect event changes within 24 hours
- Briefs pass fact vs assessment separation checks
