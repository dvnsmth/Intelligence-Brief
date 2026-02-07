"""
Demo script to show the platform working end-to-end.
"""

from src.pipeline import IntelligencePipeline
from src.config import get_config


def main():
    print("="*70)
    print("Geopolitical Risk Intelligence Platform - Demo")
    print("="*70)
    print()
    
    pipeline = IntelligencePipeline()
    config = get_config()
    
    # Run pipeline
    print("Running full pipeline...")
    print("-"*70)
    results = pipeline.run_full_pipeline()
    print()
    
    # Show results summary
    print("="*70)
    print("Pipeline Results Summary")
    print("="*70)
    print(f"Ingested sources: {results['ingested']}")
    print(f"Normalized sources: {results['normalized']}")
    print(f"Source clusters: {results['clusters']}")
    print(f"Extracted events: {results['events']}")
    print(f"Assessments created: {results['assessments']}")
    print(f"Briefs generated: {results['briefs']}")
    print()
    
    # Show example query for a monitored country
    if config.monitored_countries:
        example_country = config.monitored_countries[0]
        print("="*70)
        print(f"Example Query: {example_country}")
        print("="*70)
        print()
        
        result = pipeline.answer_query(example_country)
        
        if result['assessment']:
            print("ASSESSMENT:")
            print(f"  Overall Score: {result['assessment'].overall_score:.1f}/100")
            print(f"  Delta (7d): {result['assessment'].delta_7d:+.1f}")
            print()
            
            print("Sub-scores:")
            for sub_score in result['assessment'].sub_scores:
                print(f"  {sub_score.name}: {sub_score.value:.1f}/100")
            print()
        
        if result['brief']:
            print("BRIEF:")
            print(f"What Changed: {result['brief'].what_changed[:200]}...")
            print()
            print(f"Why It Matters: {result['brief'].why_it_matters[:200]}...")
            print()
        
        if result['events']:
            print(f"RECENT EVENTS ({len(result['events'])}):")
            for event in result['events'][:3]:
                print(f"  - {event.event_type.value}: {event.summary[:100]}...")
                print(f"    Location: {event.location}, Confidence: {event.confidence_label.value}")
            print()
    
    print("="*70)
    print("Demo complete!")
    print("="*70)
    print()
    print("Try these commands:")
    print(f"  python cli.py query \"{example_country}\"")
    print(f"  python cli.py assessment \"{example_country}\"")
    print(f"  python cli.py brief \"{example_country}\"")
    print()
    print("Or start the API server:")
    print("  python -m src.api")
    print("  Then visit: http://127.0.0.1:5000/api/query/" + example_country.replace(" ", "%20"))


if __name__ == '__main__':
    main()
