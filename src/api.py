"""
Simple API for querying assessments, events, and briefs.
Uses Flask for MVP.
"""

from flask import Flask, jsonify, request
from typing import Dict, Any, Optional

from .pipeline import IntelligencePipeline
from .storage import Storage
from .models import Assessment, Brief, Event


app = Flask(__name__)
pipeline = IntelligencePipeline()


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
        'timestamp': event.timestamp.isoformat(),
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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'intelligence-brief'})


if __name__ == '__main__':
    config = pipeline.config
    app.run(
        host=config.api.get('host', '127.0.0.1'),
        port=config.api.get('port', 5000),
        debug=config.api.get('debug', False)
    )
