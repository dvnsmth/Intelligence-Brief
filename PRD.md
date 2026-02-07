# Product Requirements Document (PRD)

## 1. Problem Definition (Locked)

### Problem statement
Global decision makers face fragmented, fast-moving geopolitical information with inconsistent quality and unclear sourcing. This platform turns diverse inputs into verified, decision-ready intelligence with transparent sources, confidence labeling, and explainable risk scoring.

It is designed to support operational and strategic decisions by separating facts from assessments, avoiding narrative amplification, and providing traceable evidence for every claim. It is not a prediction engine or a tactical intelligence system.

### Primary user personas
- Executive decision makers (CEO/CRO/COO) needing concise briefings
- Geopolitical and security analysts requiring evidence-rich context
- Supply-chain and operations leaders monitoring disruption risk
- Investors and portfolio managers assessing country exposure
- Compliance and risk officers tracking sanctions and stability changes

### In-scope decisions
- Operational risk mitigation (rerouting, security posture adjustments)
- Market exposure adjustments (country or sector rebalancing)
- Compliance actions (sanctions exposure monitoring)
- Scenario planning inputs (contingency planning)

### Out-of-scope decisions (non-goals)
- Tactical battlefield intelligence or targeting
- Individual-level surveillance or personal profiling
- Automated trading signals or execution
- Deterministic predictions of specific events or dates

## 2. Product Outputs (User-Facing)

### 2.1 Situation Briefs
**Structure**
- What changed (facts, sourced)
- Why it matters (assessment, sourced or explicitly marked)
- What to watch (scenarios + indicators, not predictions)

**Length targets**
- Executive: 200 to 350 words
- Analyst: 600 to 900 words

**Citation and confidence requirements**
- Minimum 2 independent sources per critical fact
- Inline citations per paragraph
- Confidence label per claim: High / Medium / Low

**Acceptance criteria**
- Each brief includes at least 3 citations and explicit confidence markers.
- The "What changed" section is purely factual with timestamps.

### 2.2 Risk and Stability Scorecards
**Overall score definition**
- Composite index: 0 to 100 (higher = more stable / lower risk)

**Required sub-scores**
- Political stability
- Security and conflict risk
- Economic resilience
- Social cohesion
- Governance and rule of law
- External relations and sanctions exposure
- Financial risk

**Time-based trend indicators**
- 7-day, 30-day, 90-day deltas vs baseline
- Volatility indicator (signal variance)

**Acceptance criteria**
- Each score is traceable to contributing signals with weights and confidence.
- Scorecards show current value, delta, and key drivers.

### 2.3 Event Timeline
**What qualifies as an event**
- Verified occurrence with time, place, and actor
- At least one credible source plus a corroborating signal

**Required metadata per event**
- Timestamp (ISO 8601)
- Location (geo-coded)
- Event type
- Entities involved
- Source list with credibility tier
- Confidence score
- Impact tags (trade, security, infrastructure)

**Acceptance criteria**
- Each event includes at least one source and a confidence score.
- Duplicate and near-duplicate events are merged.

### 2.4 Alerts
**Trigger logic**
- Score threshold breach
- Significant delta (example: 10-point drop in 7 days)
- Pattern detection (escalation sequence)

**Delivery expectations**
- UI dashboard
- Email notifications
- Optional webhook for integrations

**Acceptance criteria**
- Alert includes trigger cause, relevant evidence, and confidence.
- Alerts are deduplicated and rate-limited.

## 3. Data Ingestion and Sources

### Source categories
- Government and official releases
- Tier-1 media with editorial standards
- Regional media with known reliability
- Structured datasets (economic, conflict, sanctions)
- Industry feeds (energy, logistics, finance)
- Social/OSINT (weak signals only)

### Minimum viable sources (MVP)
- Official government releases (US, EU, UK, UN)
- Tier-1 media (Reuters, AP, Bloomberg)
- Structured datasets (World Bank, IMF, UN, ACLED)
- Sanctions lists (OFAC, EU, UK HM Treasury)

### Source credibility tiers and weighting
- Tier A: Official sources, verified datasets (highest weight)
- Tier B: Tier-1 media, reputable NGOs
- Tier C: Regional outlets with known reliability
- Tier D: Social or unverified (cannot confirm alone)

### Raw data retention requirements
- Store raw text, metadata, URLs, timestamps, and provenance
- Preserve original language and translated versions

### Explicit handling requirements
- **Multilingual:** detect language, translate for analysis, store originals
- **Duplication:** semantic clustering and shared-source detection
- **Update frequency:** hourly for high-priority regions, daily otherwise

## 4. Normalization and Intelligence Pipeline (User-Facing Impact)
- Ingestion
- Language detection and translation
- Entity recognition and resolution
- Story clustering and deduplication
- Event extraction
- Confidence scoring
- Storage (raw / derived / assessments)

User-facing impact: all outputs are sourced, deduplicated, and confidence-labeled, with fact-assessment separation.

## 5. Event and Entity Model (Foundational)

### Event definition
A discrete occurrence with a known time, place, actors, and type, supported by credible sources and corroboration.

### Event taxonomy v0.1 (initial)
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
- Financial Risk and Security

### Entity types
- Country and region
- City and location
- Political leader and government agency
- Armed group or militia
- Corporation or state-owned enterprise
- Infrastructure asset
- International organization

## 6. Risk and Stability Scoring Framework (Product View)

### Requirements
- Explainable scoring with traceable drivers
- Configurable weights without redeploy
- Supports historical backtesting later

### Conceptual scoring formula
OverallScore = sum(w_i * S_i * C_i)

### Sub-scores and drivers
- Political: leadership changes, governance instability
- Security: conflict events, armed incidents
- Economic: inflation shocks, currency volatility
- Social: protests, displacement
- Governance: corruption and rule-of-law shifts
- External: sanctions exposure, diplomatic disputes

### Deltas and baselines
- 7/30/90-day deltas vs 12-month baseline
- Volatility indicator for signal variance

### Uncertainty handling
- Low confidence reduces weight
- Events with confidence < 0.4 go to watchlist only

## 7. Summarization and Analysis Rules

### Rules
- Separate facts and assessments
- Use likelihood bands, avoid predictions
- Cite every factual claim
- Neutral, non-alarmist tone
- Do not assert causality without evidence

### Example good excerpt
Fact: "Protests occurred in City A on Feb 6, involving ~5,000 people." (Source A, Source B) Confidence: High.
Assessment: "This elevates short-term social unrest risk (Medium likelihood) if security forces respond aggressively." Indicators: security posture changes, protest permits denied.

### Example bad excerpt
"The government will likely collapse within weeks." (Uncited, speculative)

## 8. System Guardrails (Critical)
- Narrative amplification prevention via deduplication and unique-source limits
- Source flooding control with caps per outlet and shared-source detection
- Low-credibility dominance blocked (Tier D cannot confirm alone)
- Causality enforcement: require explicit evidence
- Over-precision prevention: use likelihood bands only

## 9. MVP Scope and Phased Roadmap

### MVP wedge
- Country stability monitoring for G20 + top 10 trade partners

### Phase 1 (MVP)
- Tier A/B sources only
- 10 core event types
- Scorecards + briefs for top 30 countries
- UI dashboard + email alerts

### Phase 2 (v1)
- Expanded sources including Tier C
- Broader event taxonomy
- Advanced entity resolution
- API access

### Phase 3 (Mature)
- Full multilingual analytics
- Sector-specific risk models
- Scenario simulations with backtesting
- Enterprise governance and audit logs

### Phase advancement criteria
- MVP to v1: >=85 percent event precision, stable scoring, adoption
- v1 to mature: proven accuracy, backtesting coverage, scale readiness

## 10. Open Questions and Assumptions

### Assumptions
- Licensing access to Tier-1 sources is available
- Legal clearance for structured datasets
- Users prefer explainable scoring

### Unknowns requiring decision
- Priority regions for MVP
- Licensing budget for premium feeds
- Preferred delivery channels (email, Slack, API)

### Decisions altering architecture
- Real-time vs batch processing
- SaaS multi-tenant vs single-tenant
- Data separation vs shared models

### Decision checklist
- Priority region list
- Source licensing commitments
- MVP output format (dashboard vs briefs)
- Governance requirements (audit logs, compliance)
