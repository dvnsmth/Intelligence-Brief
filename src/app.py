"""
Web application for the Geopolitical Risk Intelligence Platform.
Serves HTML pages and API endpoints.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import json
import time

from .pipeline import IntelligencePipeline
from .storage import Storage
from .models import Assessment, Brief, Event
from .config import get_config

# Log path for debugging
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.cursor', 'debug.log')


app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# #region agent log
try:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(json.dumps({"id":"log_app_created","timestamp":int(time.time()*1000),"location":"app.py:22","message":"Flask app instance created","data":{"app_name":app.name,"app_id":id(app),"template_folder":"../templates","static_folder":"../static"},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
except: pass
# #endregion

# Add request logging middleware
@app.before_request
def log_request():
    # #region agent log
    print(f"[DEBUG] Request received: {request.method} {request.path}")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps({"id":"log_request","timestamp":int(time.time()*1000),"location":"app.py:before_request","message":"Request received","data":{"path":request.path,"method":request.method,"app_name":app.name,"app_id":id(app)},"runId":"pre-fix","hypothesisId":"B"}) + "\n")
    except Exception as e:
        print(f"[DEBUG] Error logging request: {e}")
        pass
    # #endregion

@app.errorhandler(404)
def handle_404(e):
    # #region agent log
    routes = [r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')]
    print(f"[DEBUG] 404 Error - Path: {request.path}, Routes: {routes}, /map in routes: {'/map' in routes}")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps({"id":"log_404_error","timestamp":int(time.time()*1000),"location":"app.py:handle_404","message":"404 error","data":{"path":request.path,"method":request.method,"app_name":app.name,"app_id":id(app),"registered_routes":routes,"map_in_routes":"/map" in routes},"runId":"pre-fix","hypothesisId":"B"}) + "\n")
    except Exception as log_err:
        print(f"[DEBUG] Error logging 404: {log_err}")
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"id":"log_404_log_error","timestamp":int(time.time()*1000),"location":"app.py:handle_404","message":"Error logging 404","data":{"error":str(log_err)},"runId":"pre-fix","hypothesisId":"B"}) + "\n")
        except: pass
    # #endregion
    return jsonify({'error': f'Route not found: {request.path}'}), 404

# #region agent log
try:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(json.dumps({"id":"log_app_init","timestamp":int(time.time()*1000),"location":"app.py:16","message":"Flask app created","data":{"template_folder":"../templates","static_folder":"../static"},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
except: pass
# #endregion

pipeline = IntelligencePipeline()

# #region agent log
try:
    with open(log_path, 'a') as f:
        f.write(json.dumps({"id":"log_pipeline_init","timestamp":int(time.time()*1000),"location":"app.py:20","message":"Pipeline initialized","data":{},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
except: pass
# #endregion


def _serialize_assessment(assessment: Assessment) -> Dict[str, Any]:
    """Serialize assessment to dict"""
    return {
        'assessment_id': assessment.assessment_id,
        'target': assessment.target,
        'overall_score': assessment.overall_score,
        'sub_scores': [
            {
                'name': s.name,
                'value': s.value,
                'delta_7d': s.delta_7d,
                'delta_30d': s.delta_30d,
                'delta_90d': s.delta_90d
            }
            for s in assessment.sub_scores
        ],
        'delta_7d': assessment.delta_7d,
        'delta_30d': assessment.delta_30d,
        'delta_90d': assessment.delta_90d,
        'drivers': assessment.drivers,
        'confidence': assessment.confidence,
        'generated_at': assessment.generated_at.isoformat()
    }


def _serialize_brief(brief: Brief) -> Dict[str, Any]:
    """Serialize brief to dict"""
    return {
        'brief_id': brief.brief_id,
        'target': brief.target,
        'what_changed': brief.what_changed,
        'why_it_matters': brief.why_it_matters,
        'what_to_watch': brief.what_to_watch,
        'citations': [
            {
                'url': c.url,
                'title': c.title,
                'source_name': c.source_name,
                'tier': c.tier.value
            }
            for c in brief.citations
        ],
        'confidence_markers': {
            k: v.value for k, v in brief.confidence_markers.items()
        },
        'generated_at': brief.generated_at.isoformat(),
        'brief_type': brief.brief_type
    }


def _serialize_event(event: Event) -> Dict[str, Any]:
    """Serialize event to dict"""
    return {
        'event_id': event.event_id,
        'event_type': event.event_type.value,
        'timestamp': event.timestamp,  # Keep as datetime for template
        'timestamp_str': event.timestamp.strftime('%Y-%m-%d %H:%M') if event.timestamp else 'N/A',
        'location': event.location,
        'summary': event.summary,
        'confidence': event.confidence,
        'confidence_label': event.confidence_label.value,
        'sources': [
            {
                'url': s.url,
                'title': s.title,
                'source_name': s.source_name,
                'tier': s.tier.value
            }
            for s in event.sources
        ],
        'impact_tags': event.impact_tags
    }


# Web UI Routes

@app.route('/')
def index():
    """Home page - dashboard"""
    config = get_config()
    countries = config.monitored_countries[:20]  # Show top 20
    
    # Get assessments for each country
    country_data = []
    for country in countries:
        assessment = pipeline.get_assessment(country)
        if assessment:
            country_data.append({
                'name': country,
                'score': assessment.overall_score,
                'delta_7d': assessment.delta_7d
            })
        else:
            country_data.append({
                'name': country,
                'score': None,
                'delta_7d': 0
            })
    
    # Sort by score (lowest first - most risky)
    country_data.sort(key=lambda x: x['score'] if x['score'] is not None else 100)
    
    return render_template('index.html', countries=country_data)


@app.route('/region/<target>')
def region_detail(target: str):
    """Region detail page"""
    result = pipeline.answer_query(target)
    
    # Serialize events and brief for template
    serialized_events = [_serialize_event(e) for e in result['events']] if result['events'] else []
    serialized_brief = _serialize_brief(result['brief']) if result['brief'] else None
    
    return render_template('region.html',
                         target=target,
                         assessment=result['assessment'],
                         events=serialized_events,
                         brief=serialized_brief)


@app.route('/map')
def map_view():
    """Map view page"""
    # #region agent log
    print("[DEBUG] map_view() function called!")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps({"id":"log_map_route_called","timestamp":int(time.time()*1000),"location":"app.py:map_view","message":"Map view route called","data":{},"runId":"pre-fix","hypothesisId":"B"}) + "\n")
    except Exception as e:
        print(f"[DEBUG] Error logging map_view call: {e}")
        pass
    # #endregion
    
    try:
        # #region agent log
        try:
            template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'map.html')
            with open(log_path, 'a') as f:
                f.write(json.dumps({"id":"log_map_template_render","timestamp":int(time.time()*1000),"location":"app.py:map_view","message":"Rendering map.html template","data":{"template_exists":os.path.exists(template_path),"template_path":template_path},"runId":"pre-fix","hypothesisId":"C"}) + "\n")
        except Exception as log_err: pass
        # #endregion
        
        result = render_template('map.html')
        
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"id":"log_map_template_success","timestamp":int(time.time()*1000),"location":"app.py:map_view","message":"Template rendered successfully","data":{"result_length":len(result) if result else 0},"runId":"pre-fix","hypothesisId":"C"}) + "\n")
        except: pass
        # #endregion
        
        return result
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"id":"log_map_template_error","timestamp":int(time.time()*1000),"location":"app.py:map_view","message":"Template render error","data":{"error":str(e),"error_type":type(e).__name__},"runId":"pre-fix","hypothesisId":"C"}) + "\n")
        except: pass
        # #endregion
        raise


@app.route('/api/map-data', methods=['GET'])
def map_data_endpoint():
    """Get events and country data for map visualization"""
    # #region agent log
    print(f"[DEBUG] map_data_endpoint() called - type={request.args.get('type', '')}, days={request.args.get('days', 90)}")
    # #endregion
    
    try:
        event_type = request.args.get('type', '')
        days = int(request.args.get('days', 90))
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all events
        all_events = []
        config = get_config()
        # #region agent log
        print(f"[DEBUG] Monitored countries: {config.monitored_countries[:5]}...")
        # #endregion
        
        for country in config.monitored_countries:
            try:
                events = pipeline.get_events(country, limit=50)
                all_events.extend(events)
            except Exception as e:
                print(f"[DEBUG] Error getting events for {country}: {e}")
                continue
        
        # #region agent log
        print(f"[DEBUG] Total events retrieved: {len(all_events)}")
        # #endregion
        
        # Filter by type and date
        filtered_events = []
        for event in all_events:
            if event_type and event.event_type.value != event_type:
                continue
            if event.timestamp < cutoff_date:
                continue
            filtered_events.append(_serialize_event(event))
        
        # #region agent log
        print(f"[DEBUG] Filtered events: {len(filtered_events)}")
        # #endregion
        
        # Get country scores
        countries_data = []
        for country in config.monitored_countries[:30]:
            try:
                assessment = pipeline.get_assessment(country)
                if assessment:
                    countries_data.append({
                        'name': country,
                        'score': assessment.overall_score
                    })
            except Exception as e:
                print(f"[DEBUG] Error getting assessment for {country}: {e}")
                continue
        
        # #region agent log
        print(f"[DEBUG] Countries data: {len(countries_data)}")
        # #endregion
        
        result = {
            'events': filtered_events,
            'countries': countries_data
        }
        
        # #region agent log
        print(f"[DEBUG] Returning map data: {len(result['events'])} events, {len(result['countries'])} countries")
        # #endregion
        
        return jsonify(result)
    except Exception as e:
        # #region agent log
        print(f"[ERROR] Error in map_data_endpoint: {e}")
        import traceback
        traceback.print_exc()
        # #endregion
        return jsonify({'error': str(e), 'events': [], 'countries': []}), 500


@app.route('/run-pipeline', methods=['POST'])
def run_pipeline():
    """Run the full pipeline"""
    try:
        results = pipeline.run_full_pipeline()
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# API Routes (for AJAX)

@app.route('/api/assessment/<target>', methods=['GET'])
def get_assessment_endpoint(target: str):
    """Get assessment for a target"""
    assessment = pipeline.get_assessment(target)
    if not assessment:
        return jsonify({'error': f'No assessment found for {target}'}), 404
    
    return jsonify(_serialize_assessment(assessment))


@app.route('/api/brief/<target>', methods=['GET'])
def get_brief_endpoint(target: str):
    """Get brief for a target"""
    brief_type = request.args.get('type', 'executive')
    brief = pipeline.get_brief(target, brief_type)
    if not brief:
        return jsonify({'error': f'No brief found for {target}'}), 404
    
    return jsonify(_serialize_brief(brief))


@app.route('/api/events/<target>', methods=['GET'])
def get_events_endpoint(target: str):
    """Get events for a target"""
    limit = int(request.args.get('limit', 20))
    events = pipeline.get_events(target, limit=limit)
    
    return jsonify({
        'target': target,
        'events': [_serialize_event(e) for e in events],
        'count': len(events)
    })


@app.route('/api/query/<target>', methods=['GET'])
def query_endpoint(target: str):
    """
    Answer: What is happening in X region right now, why does it matter,
    how risky is it, and what evidence supports that assessment?
    """
    result = pipeline.answer_query(target)
    
    return jsonify({
        'target': result['target'],
        'assessment': _serialize_assessment(result['assessment']) if result['assessment'] else None,
        'events': [_serialize_event(e) for e in result['events']],
        'brief': _serialize_brief(result['brief']) if result['brief'] else None,
        'timestamp': result['timestamp']
    })


@app.route('/api/trends/<target>', methods=['GET'])
def trends_endpoint(target: str):
    """Get historical trends for a target"""
    from datetime import datetime, timedelta
    
    historical = pipeline.storage.get_historical_assessments(target, days=90)
    
    trends_data = {
        'target': target,
        'scores': [
            {
                'date': a.generated_at.isoformat(),
                'score': a.overall_score,
                'sub_scores': {s.name: s.value for s in a.sub_scores}
            }
            for a in historical
        ]
    }
    
    return jsonify(trends_data)


@app.route('/api/entities/<target>', methods=['GET'])
def entities_endpoint(target: str):
    """Get entity relationships for a target"""
    from .entity_resolution import EntityResolver
    
    events = pipeline.get_events(target, limit=50)
    resolver = EntityResolver(pipeline.storage)
    relationships = resolver.build_relationships(events)
    
    return jsonify({
        'target': target,
        'relationships': relationships
    })


@app.route('/api/correlations/<event_id>', methods=['GET'])
def correlations_endpoint(event_id: str):
    """Get correlated events"""
    from .correlation import EventCorrelator
    
    event = pipeline.storage.get_event(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    correlator = EventCorrelator(pipeline.storage)
    correlated = correlator.find_correlated_events(event)
    
    return jsonify({
        'event_id': event_id,
        'correlated_events': [_serialize_event(e) for e in correlated]
    })


@app.route('/api/search', methods=['GET'])
def search_endpoint():
    """Search across events and briefs"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    # Search events
    config = get_config()
    matching_events = []
    for country in config.monitored_countries[:10]:
        events = pipeline.get_events(country, limit=20)
        for event in events:
            if (query in event.summary.lower() or 
                query in event.location.lower() or
                query in event.event_type.value.lower()):
                matching_events.append(_serialize_event(event))
    
    return jsonify({
        'query': query,
        'events': matching_events[:50],  # Limit results
        'count': len(matching_events)
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'intelligence-brief'})


if __name__ == '__main__':
    config = get_config()
    
    # #region agent log
    try:
        with open(log_path, 'a') as f:
            routes = [r.rule for r in app.url_map.iter_rules()]
            f.write(json.dumps({"id":"log_routes_registered","timestamp":int(time.time()*1000),"location":"app.py:__main__","message":"Routes registered at startup","data":{"routes":routes,"map_route_exists":"/map" in routes},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    app.run(
        host=config.api.get('host', '127.0.0.1'),
        port=config.api.get('port', 5000),
        debug=config.api.get('debug', False)
    )
