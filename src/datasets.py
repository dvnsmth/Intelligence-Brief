"""
Dataset ingestion for structured data sources (ACLED, World Bank, IMF, etc.)
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

from .models import RawSource, SourceTier, Event, EventType
from .config import get_config


class DatasetIngester:
    """Ingest structured datasets"""
    
    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Intelligence-Brief/0.1.0 (Geopolitical Risk Intelligence Platform)'
        })
    
    def fetch_datasets(self) -> List[RawSource]:
        """Fetch from all configured datasets"""
        sources = []
        datasets = self.config.sources.get('datasets', [])
        
        for dataset_config in datasets:
            if not dataset_config.get('enabled', False):
                continue
            
            try:
                if dataset_config['name'] == 'ACLED':
                    dataset_sources = self.fetch_acled(dataset_config)
                elif dataset_config['name'] == 'World Bank':
                    dataset_sources = self.fetch_world_bank(dataset_config)
                else:
                    continue
                
                sources.extend(dataset_sources)
            except Exception as e:
                print(f"Error fetching {dataset_config['name']}: {e}")
                continue
        
        return sources
    
    def fetch_acled(self, config: dict) -> List[RawSource]:
        """Fetch ACLED conflict data"""
        sources = []
        endpoint = config.get('endpoint', '')
        api_key = config.get('api_key', '')
        
        if not api_key:
            # ACLED requires registration, return empty for now
            return []
        
        try:
            # Get events from last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            params = {
                'key': api_key,
                'email': 'your-email@example.com',  # Should be in config
                'event_date': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
                'limit': 100
            }
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                for event in data.get('data', []):
                    try:
                        event_date = datetime.strptime(event.get('event_date', ''), '%Y-%m-%d')
                        
                        # Create structured content
                        content = f"Event Type: {event.get('sub_event_type', 'Unknown')}. "
                        content += f"Location: {event.get('admin1', '')}, {event.get('admin2', '')}, {event.get('country', '')}. "
                        content += f"Actors: {event.get('actor1', '')} vs {event.get('actor2', '')}. "
                        content += f"Fatalities: {event.get('fatalities', 0)}. "
                        content += f"Notes: {event.get('notes', '')}"
                        
                        source_id = f"acled_{event.get('data_id', '')}"
                        
                        raw_source = RawSource(
                            source_id=source_id,
                            url=f"https://acleddata.com/data-export-tool/",
                            title=f"ACLED Event: {event.get('sub_event_type', 'Conflict Event')} in {event.get('country', '')}",
                            content=content,
                            source_name='ACLED',
                            tier=SourceTier(config.get('tier', 'A')),
                            language='en',
                            published_at=event_date,
                            retrieved_at=datetime.utcnow(),
                            metadata={
                                'dataset': 'ACLED',
                                'event_id': event.get('data_id'),
                                'country': event.get('country'),
                                'event_type': event.get('sub_event_type'),
                                'fatalities': event.get('fatalities', 0),
                                'latitude': event.get('latitude'),
                                'longitude': event.get('longitude')
                            }
                        )
                        sources.append(raw_source)
                    except Exception as e:
                        print(f"Error processing ACLED event: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching ACLED data: {e}")
        
        return sources
    
    def fetch_world_bank(self, config: dict) -> List[RawSource]:
        """Fetch World Bank economic indicators"""
        sources = []
        endpoint = config.get('endpoint', '')
        
        # Monitor key economic indicators for geopolitical risk
        indicators = {
            'NY.GDP.MKTP.CD': 'GDP',
            'FP.CPI.TOTL.ZG': 'Inflation',
            'CM.MKT.TRAD.GD.ZS': 'Stock Market'
        }
        
        # Get data for monitored countries
        countries = self.config.monitored_countries[:10]  # Limit for API calls
        
        for indicator_code, indicator_name in indicators.items():
            try:
                # World Bank API format
                url = f"{endpoint}/country/all/indicator/{indicator_code}"
                params = {
                    'format': 'json',
                    'date': '2020:2024',
                    'per_page': 100
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list) and len(data) > 1:
                    for item in data[1]:  # Data is in second element
                        country_name = item.get('country', {}).get('value', '')
                        if country_name not in countries:
                            continue
                        
                        value = item.get('value')
                        date = item.get('date')
                        
                        if value and date:
                            content = f"World Bank {indicator_name} indicator for {country_name}: {value} (Year: {date})"
                            
                            source_id = f"wb_{indicator_code}_{country_name}_{date}"
                            
                            raw_source = RawSource(
                                source_id=source_id,
                                url=f"https://data.worldbank.org/indicator/{indicator_code}",
                                title=f"World Bank: {indicator_name} - {country_name}",
                                content=content,
                                source_name='World Bank',
                                tier=SourceTier(config.get('tier', 'A')),
                                language='en',
                                published_at=datetime(int(date), 1, 1),
                                retrieved_at=datetime.utcnow(),
                                metadata={
                                    'dataset': 'World Bank',
                                    'indicator': indicator_name,
                                    'indicator_code': indicator_code,
                                    'country': country_name,
                                    'value': value,
                                    'year': date
                                }
                            )
                            sources.append(raw_source)
            except Exception as e:
                print(f"Error fetching World Bank {indicator_name}: {e}")
                continue
        
        return sources


def ingest_datasets() -> List[RawSource]:
    """Convenience function to ingest all datasets"""
    ingester = DatasetIngester()
    return ingester.fetch_datasets()
