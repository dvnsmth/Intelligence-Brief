# Web Application Guide

## Running the Web App

### Quick Start

1. **Start the web server:**
   ```bash
   python run_web.py
   ```

2. **Open your browser:**
   Navigate to: http://127.0.0.1:5000

### Alternative: Using Flask directly

```bash
python -m src.app
```

## Features

### Dashboard (`/`)

- View all monitored countries/regions
- See stability scores at a glance
- Click any country to view details
- Run pipeline directly from the dashboard

### Region Detail Page (`/region/<target>`)

Shows comprehensive intelligence for a specific region:

1. **Risk & Stability Assessment**
   - Overall stability score (0-100)
   - 7-day, 30-day, 90-day deltas
   - Sub-scores breakdown:
     - Political stability
     - Security and conflict risk
     - Economic resilience
     - Social cohesion
     - Governance and rule of law
     - External relations

2. **Situation Brief**
   - **What Changed**: Factual summary of recent events
   - **Why It Matters**: Assessment of implications
   - **What to Watch**: Scenarios and indicators
   - **Sources**: Citations with tier labels

3. **Recent Events**
   - Chronological list of events
   - Event type, location, timestamp
   - Confidence levels
   - Impact tags
   - Source links

### Run Pipeline

Click "Run Pipeline" button to:
- Fetch latest news from RSS feeds
- Process and normalize content
- Extract events
- Calculate assessments
- Generate briefs

## API Endpoints

The web app also exposes REST API endpoints:

- `GET /api/assessment/<target>` - Get assessment JSON
- `GET /api/brief/<target>` - Get brief JSON
- `GET /api/events/<target>` - Get events JSON
- `GET /api/query/<target>` - Complete query response
- `POST /run-pipeline` - Run full pipeline
- `GET /api/health` - Health check

## Configuration

Edit `config.yaml` to customize:

- **API settings**: Change host/port
- **Monitored countries**: Add/remove regions
- **Scoring weights**: Adjust risk calculation
- **Sources**: Add RSS feeds

## Troubleshooting

### Port Already in Use

If port 5000 is taken, edit `config.yaml`:

```yaml
api:
  port: 5001  # Change to available port
```

### No Data Showing

1. Run the pipeline first (click "Run Pipeline" button)
2. Wait for processing to complete
3. Refresh the page

### Template Errors

Make sure you're running from the project root:
```bash
cd "c:\Echoes and Embers\Intelligence-Brief"
python run_web.py
```

### Static Files Not Loading

Ensure the `static/` directory exists with:
- `style.css`
- `app.js`

## Development

### File Structure

```
templates/
  base.html      # Base template
  index.html     # Dashboard
  region.html    # Region detail page

static/
  style.css      # Styles
  app.js         # JavaScript

src/
  app.py         # Flask application
```

### Adding New Pages

1. Create template in `templates/`
2. Add route in `src/app.py`
3. Update navigation in `base.html`

### Styling

Edit `static/style.css` to customize appearance.

## Production Deployment

For production:

1. Set `debug: false` in `config.yaml`
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure reverse proxy (nginx)
4. Set up SSL/TLS
5. Configure proper logging

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.app:app
```
