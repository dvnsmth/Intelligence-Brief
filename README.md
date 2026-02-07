# Geopolitical Risk Intelligence Platform

MVP implementation of a geopolitical risk intelligence platform that ingests global information, normalizes it, extracts events, assesses risk, and produces decision-ready summaries.

## Core Principles

- **Transparent sourcing**: Every claim is traceable to sources
- **Fact/Assessment separation**: Clear distinction between facts and analysis
- **Explainable scoring**: Risk scores are transparent and configurable
- **Deduplication**: Prevents narrative amplification and duplicate counting
- **Confidence labeling**: Every assessment includes confidence levels

## Architecture

The system follows a layered pipeline:

1. **Ingestion** → Fetch from RSS feeds and APIs
2. **Normalization** → Language detection, entity extraction, deduplication
3. **Event Extraction** → Convert content to structured events
4. **Scoring** → Calculate risk and stability scores
5. **Summarization** → Generate briefs with fact/assessment separation
6. **Storage** → Separate raw, derived, and assessment layers
7. **Presentation** → API and CLI interfaces

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
cd "c:\Echoes and Embers\Intelligence-Brief"
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: Some optional dependencies (like `googletrans`) may have limitations. The system will work without full translation support for MVP.

## Usage

### Run the Full Pipeline

Process all sources and generate assessments:

```bash
python cli.py run
```

This will:
- Fetch from configured RSS feeds
- Normalize and deduplicate sources
- Extract events
- Calculate assessments for monitored countries
- Generate briefs

### Query a Region

Get a complete intelligence report for a region:

```bash
python cli.py query "United States"
```

Output includes:
- Current risk/stability assessment
- Recent events
- Situation brief

### Get Assessment

```bash
python cli.py assessment "China"
```

### Get Brief

```bash
python cli.py brief "Germany" --type executive
```

### Get Events

```bash
python cli.py events "Japan" --limit 10
```

### Web Application

Start the web app:
```bash
python run_web.py
```

Then open your browser:
- http://127.0.0.1:5000 - Dashboard with country scores
- http://127.0.0.1:5000/region/United%20States - Detailed region view

The web app provides:
- Interactive dashboard with country stability scores
- Detailed region pages with assessments, briefs, and events
- One-click pipeline execution
- Beautiful, responsive UI

### API Server (Alternative)

For API-only access:
```bash
python -m src.api
```

Then query endpoints:

- `GET /api/assessment/<target>` - Get assessment
- `GET /api/brief/<target>` - Get brief
- `GET /api/events/<target>` - Get events
- `GET /api/query/<target>` - Complete query response
- `GET /api/health` - Health check

Example:
```bash
curl http://127.0.0.1:5000/api/query/United%20States
```

## Configuration

Edit `config.yaml` to:

- Adjust scoring weights
- Add/remove sources
- Configure deduplication thresholds
- Modify monitored countries

## Testing

Run tests:

```bash
pytest tests/
```

Test coverage includes:
- Deduplication/clustering logic
- Event extraction
- Score calculation

## Data Storage

Data is stored in SQLite database at `data/intelligence_brief.db` (configurable).

Tables:
- `raw_sources` - Original ingested content
- `events` - Extracted structured events
- `assessments` - Risk/stability scores
- `briefs` - Generated situation briefs
- `entities` - Canonical entity records

## MVP Scope

This MVP includes:

- ✅ RSS feed ingestion (Reuters, AP News)
- ✅ Basic language detection
- ✅ Country/region entity extraction
- ✅ Story clustering and deduplication
- ✅ Event type detection (16 types)
- ✅ Rule-based scoring with configurable weights
- ✅ Brief generation with fact/assessment separation
- ✅ SQLite storage
- ✅ CLI and API interfaces

## Limitations (MVP)

- Translation support is basic (relies on optional dependencies)
- Entity extraction uses simple pattern matching (not full NER)
- Deduplication uses text similarity (not semantic embeddings)
- Scoring is rule-based (not ML-based)
- Historical deltas are simplified (would need time-series queries in production)

## Project Structure

```
Intelligence-Brief/
├── src/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── config.py          # Configuration management
│   ├── storage.py          # Database layer
│   ├── ingestion.py        # Source fetching
│   ├── normalization.py    # Language/entity/deduplication
│   ├── event_extraction.py # Event creation
│   ├── scoring.py          # Risk scoring
│   ├── summarization.py    # Brief generation
│   ├── pipeline.py         # Main orchestrator
│   └── api.py              # Flask API
├── tests/
│   ├── test_deduplication.py
│   ├── test_event_extraction.py
│   └── test_scoring.py
├── config.yaml             # Configuration
├── cli.py                  # Command-line interface
├── requirements.txt        # Dependencies
└── README.md
```

## Answering the Core Query

The system is designed to answer:

> "What is happening in X region right now, why does it matter, how risky is it, and what evidence supports that assessment?"

Use:
```bash
python cli.py query "<region>"
```

Or via API:
```bash
curl http://127.0.0.1:5000/api/query/<region>
```

## License

See repository for license information.
