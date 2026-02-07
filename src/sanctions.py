"""
Sanctions list ingestion (OFAC, EU, UK HM Treasury)
"""

import requests
from datetime import datetime
from typing import List, Dict, Any
import csv
import xml.etree.ElementTree as ET
from io import StringIO

from .models import RawSource, SourceTier
from .config import get_config


class SanctionsIngester:
    """Ingest sanctions lists"""
    
    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Intelligence-Brief/0.1.0 (Geopolitical Risk Intelligence Platform)'
        })
    
    def fetch_sanctions(self) -> List[RawSource]:
        """Fetch from all configured sanctions sources"""
        sources = []
        sanctions_configs = self.config.sources.get('sanctions', [])
        
        for sanctions_config in sanctions_configs:
            if not sanctions_config.get('enabled', False):
                continue
            
            try:
                if 'OFAC' in sanctions_config['name']:
                    sanctions_sources = self.fetch_ofac(sanctions_config)
                elif 'EU' in sanctions_config['name']:
                    sanctions_sources = self.fetch_eu_sanctions(sanctions_config)
                elif 'UK' in sanctions_config['name']:
                    sanctions_sources = self.fetch_uk_sanctions(sanctions_config)
                else:
                    continue
                
                sources.extend(sanctions_sources)
            except Exception as e:
                print(f"Error fetching {sanctions_config['name']}: {e}")
                continue
        
        return sources
    
    def fetch_ofac(self, config: dict) -> List[RawSource]:
        """Fetch OFAC sanctions list"""
        sources = []
        
        # OFAC provides XML/CSV downloads
        # For MVP, we'll parse a sample structure
        # In production, would download actual files
        
        try:
            # OFAC SDN (Specially Designated Nationals) list URL
            # Note: Actual implementation would download and parse the XML file
            url = "https://ofac.treasury.gov/ofac-sanctions-list-downloads"
            
            # Create a sample source indicating sanctions monitoring
            # In production, would parse actual OFAC XML/CSV files
            content = "OFAC sanctions list monitoring. Check official OFAC website for current listings."
            
            source_id = f"ofac_monitor_{datetime.utcnow().strftime('%Y%m%d')}"
            
            raw_source = RawSource(
                source_id=source_id,
                url=url,
                title="OFAC Sanctions List Monitoring",
                content=content,
                source_name='OFAC',
                tier=SourceTier(config.get('tier', 'A')),
                language='en',
                published_at=datetime.utcnow(),
                retrieved_at=datetime.utcnow(),
                metadata={
                    'sanctions_source': 'OFAC',
                    'list_type': 'SDN',
                    'note': 'Full parsing requires downloading OFAC XML files'
                }
            )
            sources.append(raw_source)
        except Exception as e:
            print(f"Error fetching OFAC sanctions: {e}")
        
        return sources
    
    def fetch_eu_sanctions(self, config: dict) -> List[RawSource]:
        """Fetch EU sanctions"""
        sources = []
        
        try:
            # EU Sanctions Map API (if available)
            # For MVP, use RSS feed or structured data
            url = "https://www.sanctionsmap.eu/"
            
            content = "EU sanctions monitoring. Check EU Sanctions Map for current listings."
            
            source_id = f"eu_sanctions_{datetime.utcnow().strftime('%Y%m%d')}"
            
            raw_source = RawSource(
                source_id=source_id,
                url=url,
                title="EU Sanctions Monitoring",
                content=content,
                source_name='EU Sanctions',
                tier=SourceTier(config.get('tier', 'A')),
                language='en',
                published_at=datetime.utcnow(),
                retrieved_at=datetime.utcnow(),
                metadata={
                    'sanctions_source': 'EU',
                    'note': 'Full parsing requires EU Sanctions Map API access'
                }
            )
            sources.append(raw_source)
        except Exception as e:
            print(f"Error fetching EU sanctions: {e}")
        
        return sources
    
    def fetch_uk_sanctions(self, config: dict) -> List[RawSource]:
        """Fetch UK HM Treasury sanctions"""
        sources = []
        
        try:
            url = "https://www.gov.uk/government/collections/financial-sanctions-regime-specific-consolidated-lists-and-releases"
            
            content = "UK HM Treasury sanctions monitoring. Check UK government website for current listings."
            
            source_id = f"uk_sanctions_{datetime.utcnow().strftime('%Y%m%d')}"
            
            raw_source = RawSource(
                source_id=source_id,
                url=url,
                title="UK HM Treasury Sanctions Monitoring",
                content=content,
                source_name='UK HM Treasury',
                tier=SourceTier(config.get('tier', 'A')),
                language='en',
                published_at=datetime.utcnow(),
                retrieved_at=datetime.utcnow(),
                metadata={
                    'sanctions_source': 'UK',
                    'note': 'Full parsing requires downloading UK sanctions lists'
                }
            )
            sources.append(raw_source)
        except Exception as e:
            print(f"Error fetching UK sanctions: {e}")
        
        return sources


def ingest_sanctions() -> List[RawSource]:
    """Convenience function to ingest sanctions lists"""
    ingester = SanctionsIngester()
    return ingester.fetch_sanctions()
