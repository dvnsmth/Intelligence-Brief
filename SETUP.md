# Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the demo:**
   ```bash
   python demo.py
   ```

3. **Or run the full pipeline:**
   ```bash
   python cli.py run
   ```

4. **Query a region:**
   ```bash
   python cli.py query "United States"
   ```

## First Run

On first run, the system will:
- Create the database at `data/intelligence_brief.db`
- Fetch news from configured RSS feeds (Reuters, AP News)
- Process and normalize the content
- Extract events
- Calculate assessments
- Generate briefs

This may take a few minutes depending on network speed and number of sources.

## Configuration

Edit `config.yaml` to customize:
- Scoring weights
- Source feeds
- Monitored countries
- Deduplication thresholds

## API Server

Start the API:
```bash
python -m src.api
```

Then access:
- http://127.0.0.1:5000/api/health
- http://127.0.0.1:5000/api/query/United%20States

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the project root:
```bash
cd "c:\Echoes and Embers\Intelligence-Brief"
python cli.py run
```

### RSS Feed Issues

If RSS feeds fail to fetch:
- Check your internet connection
- Some feeds may require authentication (not implemented in MVP)
- Try updating feed URLs in `config.yaml`

### Database Issues

If you encounter database errors:
- Delete `data/intelligence_brief.db` to reset
- Ensure the `data/` directory is writable

### Translation Warnings

If you see warnings about translation:
- This is expected - full translation requires additional setup
- The system works with English sources for MVP
- Language detection still works for basic classification

## Testing

Run tests:
```bash
pytest tests/
```

## Next Steps

After setup:
1. Review generated assessments: `python cli.py assessment "Country"`
2. Read briefs: `python cli.py brief "Country"`
3. Explore events: `python cli.py events "Country"`
4. Customize `config.yaml` for your needs
