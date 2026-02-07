"""
Ingestion layer for fetching data from various sources.
Supports RSS feeds and APIs for MVP.
"""

import feedparser
import requests
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin
import hashlib
import re
from bs4 import BeautifulSoup

from .models import RawSource, SourceTier
from .config import get_config


class IngestionService:
    """Service for ingesting data from configured sources"""
    
    def __init__(self):
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Intelligence-Brief/0.1.0 (Geopolitical Risk Intelligence Platform)'
        })
    
    def fetch_all_sources(self) -> List[RawSource]:
        """Fetch from all configured sources"""
        sources = []
        
        # Fetch RSS feeds
        feeds = self.config.sources.get('feeds', [])
        for feed_config in feeds:
            try:
                feed_sources = self.fetch_feed(feed_config)
                sources.extend(feed_sources)
            except Exception as e:
                print(f"Error fetching {feed_config['name']}: {e}")
                continue
        
        # Fetch from News APIs
        for api_config in self.config.sources.get('apis', []):
            if api_config.get('enabled', False):
                try:
                    if api_config.get('type') == 'news_api':
                        api_sources = self.fetch_news_api(api_config)
                    elif api_config.get('type') == 'guardian_api':
                        api_sources = self.fetch_guardian_api(api_config)
                    else:
                        continue
                    sources.extend(api_sources)
                except Exception as e:
                    print(f"Error fetching {api_config['name']}: {e}")
                    continue
        
        return sources
    
    def fetch_feed(self, feed_config: dict) -> List[RawSource]:
        """Fetch from an RSS feed"""
        url = feed_config['url']
        tier_str = feed_config.get('tier', 'B')
        tier = SourceTier(tier_str)
        source_name = feed_config['name']
        
        # Parse RSS feed
        feed = feedparser.parse(url)
        
        sources = []
        for entry in feed.entries:
            try:
                # Extract content
                content = self._extract_content(entry)
                
                # Parse published date
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_at = datetime(*entry.updated_parsed[:6])
                
                # Get URL
                entry_url = entry.get('link', '')
                
                # Generate source ID
                source_id = self._generate_source_id(entry_url, entry.get('title', ''))
                
                # Detect language (basic - will be improved in normalization)
                language = self._detect_language_basic(content)
                
                raw_source = RawSource(
                    source_id=source_id,
                    url=entry_url,
                    title=entry.get('title', 'Untitled'),
                    content=content,
                    source_name=source_name,
                    tier=tier,
                    language=language,
                    published_at=published_at,
                    retrieved_at=datetime.utcnow(),
                    metadata={
                        'feed_url': url,
                        'entry_id': entry.get('id', ''),
                        'tags': [tag.term for tag in entry.get('tags', [])]
                    }
                )
                sources.append(raw_source)
            except Exception as e:
                print(f"Error processing entry from {source_name}: {e}")
                continue
        
        return sources
    
    def _extract_content(self, entry) -> str:
        """Extract text content from feed entry"""
        # Try different content fields
        content = ''
        
        if hasattr(entry, 'content'):
            # Multiple content blocks
            for block in entry.content:
                if hasattr(block, 'value'):
                    content += block.value + ' '
        elif hasattr(entry, 'summary'):
            content = entry.summary
        
        # If we have a link, try to fetch full content (optional, can be slow)
        # For MVP, we'll use summary/description only
        
        # Clean HTML tags
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)
        
        return content.strip()
    
    def _generate_source_id(self, url: str, title: str) -> str:
        """Generate unique source ID"""
        # Use URL + title hash for uniqueness
        combined = f"{url}|{title}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _detect_language_basic(self, text: str) -> str:
        """Basic language detection (will be improved in normalization)"""
        # Very basic: check for common patterns
        # For MVP, assume English unless we detect otherwise
        if not text:
            return 'en'
        
        # Simple heuristics
        text_lower = text.lower()
        if any(word in text_lower for word in ['el ', 'la ', 'de ', 'en ', 'y ']):
            return 'es'  # Spanish
        if any(word in text_lower for word in ['le ', 'la ', 'de ', 'et ', 'les ']):
            return 'fr'  # French
        if any(word in text_lower for word in ['der ', 'die ', 'das ', 'und ', 'ist ']):
            return 'de'  # German
        
        return 'en'  # Default to English
    
    def fetch_news_api(self, api_config: dict) -> List[RawSource]:
        """Fetch from News API (NewsAPI.org)"""
        api_key = self.config.sources.get('api_keys', {}).get('newsapi', '')
        if not api_key:
            return []
        
        sources = []
        endpoint = api_config.get('endpoint', '')
        
        # Search for geopolitical keywords
        keywords = ['conflict', 'sanctions', 'election', 'protest', 'crisis', 'diplomatic']
        
        for keyword in keywords[:3]:  # Limit to avoid rate limits
            try:
                params = {
                    'q': keyword,
                    'apiKey': api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 10
                }
                
                response = self.session.get(endpoint, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'ok':
                    for article in data.get('articles', []):
                        try:
                            published_at = None
                            if article.get('publishedAt'):
                                from dateutil.parser import parse as parse_date
                                published_at = parse_date(article['publishedAt'])
                            
                            source_id = self._generate_source_id(
                                article.get('url', ''),
                                article.get('title', '')
                            )
                            
                            raw_source = RawSource(
                                source_id=source_id,
                                url=article.get('url', ''),
                                title=article.get('title', 'Untitled'),
                                content=article.get('description', '') + ' ' + article.get('content', ''),
                                source_name=article.get('source', {}).get('name', api_config['name']),
                                tier=SourceTier(api_config.get('tier', 'B')),
                                language=self._detect_language_basic(article.get('description', '')),
                                published_at=published_at,
                                retrieved_at=datetime.utcnow(),
                                metadata={
                                    'api_source': api_config['name'],
                                    'author': article.get('author'),
                                    'keyword': keyword
                                }
                            )
                            sources.append(raw_source)
                        except Exception as e:
                            print(f"Error processing article from {api_config['name']}: {e}")
                            continue
            except Exception as e:
                print(f"Error fetching from {api_config['name']}: {e}")
                continue
        
        return sources
    
    def fetch_guardian_api(self, api_config: dict) -> List[RawSource]:
        """Fetch from Guardian API"""
        api_key = self.config.sources.get('api_keys', {}).get('guardian', '')
        if not api_key:
            return []
        
        sources = []
        endpoint = api_config.get('endpoint', '')
        
        try:
            params = {
                'api-key': api_key,
                'section': 'world',
                'page-size': 20,
                'order-by': 'newest'
            }
            
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('response', {}).get('status') == 'ok':
                for result in data.get('response', {}).get('results', []):
                    try:
                        published_at = None
                        if result.get('webPublicationDate'):
                            from dateutil.parser import parse as parse_date
                            published_at = parse_date(result['webPublicationDate'])
                        
                        source_id = self._generate_source_id(
                            result.get('webUrl', ''),
                            result.get('webTitle', '')
                        )
                        
                        raw_source = RawSource(
                            source_id=source_id,
                            url=result.get('webUrl', ''),
                            title=result.get('webTitle', 'Untitled'),
                            content=result.get('fields', {}).get('bodyText', result.get('webTitle', '')),
                            source_name='The Guardian',
                            tier=SourceTier(api_config.get('tier', 'B')),
                            language='en',
                            published_at=published_at,
                            retrieved_at=datetime.utcnow(),
                            metadata={
                                'api_source': api_config['name'],
                                'section': result.get('sectionName')
                            }
                        )
                        sources.append(raw_source)
                    except Exception as e:
                        print(f"Error processing Guardian article: {e}")
                        continue
        except Exception as e:
            print(f"Error fetching from Guardian API: {e}")
        
        return sources


def ingest_sources() -> List[RawSource]:
    """Convenience function to ingest all sources"""
    service = IngestionService()
    return service.fetch_all_sources()
