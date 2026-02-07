"""
Command-line interface for the intelligence platform.
"""

import argparse
import json
from datetime import datetime

from src.pipeline import IntelligencePipeline
from src.config import get_config


def print_assessment(assessment):
    """Print assessment in readable format"""
    if not assessment:
        print("No assessment available.")
        return
    
    print(f"\n{'='*60}")
    print(f"Assessment for: {assessment.target}")
    print(f"{'='*60}")
    print(f"\nOverall Score: {assessment.overall_score:.1f}/100")
    print(f"  Delta (7d): {assessment.delta_7d:+.1f}")
    print(f"  Delta (30d): {assessment.delta_30d:+.1f}")
    print(f"  Delta (90d): {assessment.delta_90d:+.1f}")
    print(f"  Confidence: {assessment.confidence:.2f}")
    
    print(f"\nSub-scores:")
    for sub_score in assessment.sub_scores:
        print(f"  {sub_score.name.capitalize()}: {sub_score.value:.1f}/100 "
              f"(Δ{sub_score.delta_7d:+.1f})")
    
    if assessment.drivers:
        print(f"\nTop Drivers: {', '.join(assessment.drivers[:3])}")
    
    print(f"\nGenerated: {assessment.generated_at}")


def print_brief(brief):
    """Print brief in readable format"""
    if not brief:
        print("No brief available.")
        return
    
    print(f"\n{'='*60}")
    print(f"Situation Brief: {brief.target}")
    print(f"{'='*60}")
    
    print(f"\nWHAT CHANGED (Facts):")
    print(f"{brief.what_changed}\n")
    
    print(f"WHY IT MATTERS (Assessment):")
    print(f"{brief.why_it_matters}\n")
    
    print(f"WHAT TO WATCH:")
    print(f"{brief.what_to_watch}\n")
    
    if brief.citations:
        print(f"Sources ({len(brief.citations)}):")
        for i, citation in enumerate(brief.citations[:5], 1):
            print(f"  {i}. {citation.title}")
            print(f"     {citation.url} [{citation.tier}]")
    
    print(f"\nGenerated: {brief.generated_at}")


def print_events(events):
    """Print events in readable format"""
    if not events:
        print("No events found.")
        return
    
    print(f"\n{'='*60}")
    print(f"Events ({len(events)} found)")
    print(f"{'='*60}\n")
    
    for event in events[:10]:  # Limit to 10
        print(f"[{event.timestamp.strftime('%Y-%m-%d %H:%M')}] {event.event_type.value}")
        print(f"  Location: {event.location}")
        print(f"  Summary: {event.summary}")
        print(f"  Confidence: {event.confidence_label.value} ({event.confidence:.2f})")
        print(f"  Sources: {len(event.sources)}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Geopolitical Risk Intelligence Platform CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run pipeline
    run_parser = subparsers.add_parser('run', help='Run the full pipeline')
    
    # Query
    query_parser = subparsers.add_parser('query', help='Query a region')
    query_parser.add_argument('target', help='Target country/region')
    query_parser.add_argument('--format', choices=['text', 'json'], default='text',
                              help='Output format')
    
    # Assessment
    assess_parser = subparsers.add_parser('assessment', help='Get assessment')
    assess_parser.add_argument('target', help='Target country/region')
    
    # Brief
    brief_parser = subparsers.add_parser('brief', help='Get brief')
    brief_parser.add_argument('target', help='Target country/region')
    brief_parser.add_argument('--type', choices=['executive', 'analyst'],
                             default='executive', help='Brief type')
    
    # Events
    events_parser = subparsers.add_parser('events', help='Get events')
    events_parser.add_argument('target', help='Target country/region')
    events_parser.add_argument('--limit', type=int, default=20, help='Limit results')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    pipeline = IntelligencePipeline()
    
    if args.command == 'run':
        print("Running full pipeline...")
        results = pipeline.run_full_pipeline()
        print(f"\n{'='*60}")
        print("Pipeline Complete")
        print(f"{'='*60}")
        print(f"Ingested: {results['ingested']} sources")
        print(f"Normalized: {results['normalized']} sources")
        print(f"Clusters: {results['clusters']}")
        print(f"Events: {results['events']}")
        print(f"Assessments: {results['assessments']}")
        print(f"Briefs: {results['briefs']}")
    
    elif args.command == 'query':
        result = pipeline.answer_query(args.target)
        
        if args.format == 'json':
            # Simplified JSON output
            output = {
                'target': result['target'],
                'assessment': {
                    'overall_score': result['assessment'].overall_score if result['assessment'] else None,
                    'sub_scores': {s.name: s.value for s in result['assessment'].sub_scores} if result['assessment'] else {}
                },
                'events_count': len(result['events']),
                'brief': {
                    'what_changed': result['brief'].what_changed if result['brief'] else None,
                    'why_it_matters': result['brief'].why_it_matters if result['brief'] else None
                }
            }
            print(json.dumps(output, indent=2))
        else:
            if result['assessment']:
                print_assessment(result['assessment'])
            if result['brief']:
                print_brief(result['brief'])
            if result['events']:
                print_events(result['events'])
    
    elif args.command == 'assessment':
        assessment = pipeline.get_assessment(args.target)
        print_assessment(assessment)
    
    elif args.command == 'brief':
        brief = pipeline.get_brief(args.target, args.type)
        print_brief(brief)
    
    elif args.command == 'events':
        events = pipeline.get_events(args.target, args.limit)
        print_events(events)


if __name__ == '__main__':
    main()
