#!/usr/bin/env python3
"""
Better French Max - Smart Scraper
Enhanced news scraping with automation features, deduplication, and intelligent limits
Builds on proven manual system sources and logic
"""

import os
import sys
import time
import feedparser
import requests
import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Set, Tuple
from dateutil import parser as date_parser
import threading
from pathlib import Path
from difflib import SequenceMatcher

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from automation import AUTOMATION_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ArticleMetadata:
    """Metadata for tracking article processing history"""
    first_seen: str
    last_updated: str
    processing_history: List[str]  # ['breaking_news', 'regular_update', 'ai_processed']
    source_priority: int
    quality_score: float = 0.0
    duplicate_of: Optional[str] = None  # Article hash if this is a duplicate

@dataclass
class NewsArticle:
    """Data structure for a news article with enhanced tracking"""
    # Basic article info
    title: str
    summary: str
    link: str
    published: str
    published_parsed: Optional[str]
    
    # Source information
    source_name: str
    source_url: str
    feed_url: str
    
    # Content details
    author: Optional[str]
    category: Optional[str]
    tags: List[str]
    content: Optional[str]
    
    # Media
    image_url: Optional[str]
    image_title: Optional[str]
    
    # Technical details
    guid: Optional[str]
    language: Optional[str]
    
    # Scraping metadata
    scraped_at: str
    article_hash: str
    content_hash: str  # For deduplication
    
    # Automation enhancements
    breaking_news: bool = False
    urgency_score: float = 0.0
    
    # Processing tracking
    metadata: Optional[ArticleMetadata] = None

class EnhancedDeduplicator:
    """Advanced deduplication system for articles"""
    
    def __init__(self, scraping_config: Dict[str, Any]):
        self.config = scraping_config
        self.article_cache = {}  # hash -> ArticleMetadata
        self.processed_articles = set()  # Track what's been processed
        self.similarity_cache = {}  # Cache similarity calculations
        self.cache_lock = threading.Lock()
        
    def create_content_hash(self, title: str, summary: str, content: str = "") -> str:
        """Create a hash for content-based deduplication"""
        # Normalize text for comparison
        normalized = f"{title.lower().strip()} {summary.lower().strip()}"
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = ' '.join(normalized.split())
        
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Create a cache key
        cache_key = f"{hash(text1)}_{hash(text2)}"
        
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Calculate similarity
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        # Cache the result (limit cache size)
        if len(self.similarity_cache) < 1000:
            self.similarity_cache[cache_key] = similarity
        
        return similarity
    
    def is_duplicate(self, article: NewsArticle) -> Tuple[bool, Optional[str]]:
        """Check if article is a duplicate, return (is_duplicate, original_hash)"""
        if not self.config['enable_duplicate_detection']:
            return False, None
        
        with self.cache_lock:
            # Check exact content hash first
            if self.config['hash_comparison_enabled']:
                if article.content_hash in self.article_cache:
                    return True, article.content_hash
            
            # Check title and content similarity
            title_threshold = self.config['title_similarity_threshold']
            content_threshold = self.config['similarity_threshold']
            
            for cached_hash, metadata in self.article_cache.items():
                # Skip old articles
                first_seen = datetime.fromisoformat(metadata.first_seen.replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - first_seen).total_seconds() / 3600
                
                if age_hours > self.config['cache_duration_hours']:
                    continue
                
                # Get cached article for comparison (simplified - in real implementation would store more data)
                # For now, we'll just use title similarity as primary check
                cached_title = metadata.__dict__.get('title', '')
                if cached_title:
                    title_similarity = self.calculate_similarity(article.title, cached_title)
                    
                    if title_similarity >= title_threshold:
                        return True, cached_hash
            
            return False, None
    
    def add_article(self, article: NewsArticle, processing_stage: str = "scraped"):
        """Add article to deduplication cache"""
        with self.cache_lock:
            if article.content_hash not in self.article_cache:
                self.article_cache[article.content_hash] = ArticleMetadata(
                    first_seen=article.scraped_at,
                    last_updated=article.scraped_at,
                    processing_history=[processing_stage],
                    source_priority=self._get_source_priority(article.source_name)
                )
            else:
                # Update existing entry
                metadata = self.article_cache[article.content_hash]
                metadata.last_updated = article.scraped_at
                if processing_stage not in metadata.processing_history:
                    metadata.processing_history.append(processing_stage)
    
    def _get_source_priority(self, source_name: str) -> int:
        """Get priority score for source (higher = more reliable)"""
        if source_name in self.config['high_reliability_sources']:
            return 10
        elif source_name in self.config['breaking_news_priority_sources']:
            return 8
        else:
            return 5
    
    def cleanup_old_cache(self):
        """Remove old entries from cache"""
        with self.cache_lock:
            current_time = datetime.now(timezone.utc)
            max_age_hours = self.config['cache_duration_hours']
            
            to_remove = []
            for cache_hash, metadata in self.article_cache.items():
                first_seen = datetime.fromisoformat(metadata.first_seen.replace('Z', '+00:00'))
                age_hours = (current_time - first_seen).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    to_remove.append(cache_hash)
            
            for cache_hash in to_remove:
                del self.article_cache[cache_hash]
            
            if to_remove:
                logger.debug(f"🧹 Cleaned up {len(to_remove)} old cache entries")

class SmartScraper:
    """
    Smart RSS scraper with enhanced deduplication and intelligent limits
    """
    
    def __init__(self):
        # Configuration
        self.scraping_config = AUTOMATION_CONFIG['scraping']
        
        # EXACT same feed URLs as proven manual system
        self.feed_urls = {
            # Major French Newspapers
            "Le Monde": "http://www.lemonde.fr/rss/une.xml",
            "Le Figaro": "http://www.lefigaro.fr/rss/figaro_actualites.xml",
            "Liberation": "https://www.liberation.fr/rss/",
            "Le Parisien": "https://feeds.leparisien.fr/leparisien/rss",
            "L'Express": "https://www.lexpress.fr/arc/outboundfeeds/rss/alaune.xml",
            "Le Point": "http://www.lepoint.fr/rss.xml",
            "L'Obs": "http://tempsreel.nouvelobs.com/rss.xml",
            "La Croix": "https://www.la-croix.com/RSS",
            
            # TV/Radio News
            "BFM TV": "https://www.bfmtv.com/rss/news-24-7/",
            "France Info": "https://www.francetvinfo.fr/titres.rss",
            "France Inter": "https://www.franceinter.fr/rss",
            "Europe 1": "https://www.europe1.fr/rss.xml",
            "France 24": "https://www.france24.com/fr/rss",
            "RFI": "https://rfi.fr/fr/rss",
            
            # Regional/Specialized
            "Ouest France": "https://www.ouest-france.fr/rss/une",
            "20 Minutes": "https://partner-feeds.20min.ch/rss/20minutes",
            "AFP": "https://www.afp.com/fr/actus/afp_actualite/792,31,9,7,33/feed",
            
            # Alternative/Independent
            "Mediapart": "https://www.mediapart.fr/articles/feed",
            "Brief.me": "https://brief.me/rss",
            
            # Categories from Le Monde
            "Le Monde Politique": "https://www.lemonde.fr/politique/rss_full.xml",
            "Le Monde International": "https://www.lemonde.fr/international/rss_full.xml",
            "Le Monde Economie": "https://www.lemonde.fr/economie/rss_full.xml",
            "Le Monde Culture": "https://www.lemonde.fr/culture/rss_full.xml",
            "Le Monde Sport": "https://www.lemonde.fr/sport/rss_full.xml",
            "Le Monde Sciences": "https://www.lemonde.fr/sciences/rss_full.xml",
        }
        
        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Enhanced deduplication system
        self.deduplicator = EnhancedDeduplicator(self.scraping_config)
        
        # Source tracking
        self.failed_sources = set()
        self.source_reliability = {}
        self.source_last_success = {}
        
        # Breaking news keywords from config
        self.breaking_keywords = AUTOMATION_CONFIG['scheduling']['breaking_news_keywords']
        
        # Thread safety
        self.scraping_lock = threading.Lock()
        
        logger.info("🤖 Enhanced Smart Scraper initialized")
        logger.info(f"📰 Configured sources: {len(self.feed_urls)}")
        logger.info(f"🔧 Deduplication enabled: {self.scraping_config['enable_duplicate_detection']}")
        logger.info(f"⏰ Breaking news timeframe: {self.scraping_config['breaking_news_timeframe_hours']} hours")
        logger.info(f"📊 Max articles per breaking scan: {self.scraping_config['max_total_articles_breaking']}")

    def create_article_hash(self, title: str, link: str, published: str) -> str:
        """Create unique hash for article (for exact duplicate detection)"""
        content = f"{title}{link}{published}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def create_content_hash(self, title: str, summary: str, content: str = "") -> str:
        """Create content hash for deduplication (delegated to deduplicator)"""
        return self.deduplicator.create_content_hash(title, summary, content)

    def get_time_filter(self, scan_type: str) -> datetime:
        """Get appropriate time filter based on scan type"""
        if scan_type == "breaking":
            hours = self.scraping_config['breaking_news_timeframe_hours']
        elif scan_type == "regular":
            hours = self.scraping_config['regular_update_timeframe_hours']
        else:
            hours = self.scraping_config['max_article_age_hours']
        
        return datetime.now(timezone.utc) - timedelta(hours=hours)

    def apply_article_limits(self, articles: List[NewsArticle], scan_type: str) -> List[NewsArticle]:
        """Apply intelligent article limits based on scan type and source priority"""
        if scan_type == "breaking":
            max_total = self.scraping_config['max_total_articles_breaking']
        else:
            max_total = self.scraping_config['max_total_articles_regular']
        
        # Sort by urgency score and source priority
        prioritized = sorted(articles, key=lambda x: (
            x.urgency_score,
            self.deduplicator._get_source_priority(x.source_name),
            x.published_parsed or "1970-01-01"
        ), reverse=True)
        
        # Apply total limit
        limited = prioritized[:max_total]
        
        if len(articles) > max_total:
            logger.info(f"📊 Applied {scan_type} limit: {len(limited)}/{len(articles)} articles selected")
        
        return limited

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content (same as manual system)"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def extract_image_from_entry(self, entry) -> tuple:
        """Extract image URL and title from RSS entry (same as manual system)"""
        image_url = None
        image_title = None
        
        # Check various image fields
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if 'image' in media.get('type', ''):
                    image_url = media.get('url')
                    break
        
        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get('url') if entry.media_thumbnail else None
        
        elif hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get('type', ''):
                    image_url = enclosure.get('href')
                    break
        
        # Try to extract from description/summary
        if not image_url and hasattr(entry, 'summary'):
            img_match = re.search(r'<img[^>]*src=["\']([^"\']*)["\']', entry.summary)
            if img_match:
                image_url = img_match.group(1)
        
        return image_url, image_title
    
    def calculate_urgency_score(self, title: str, summary: str) -> float:
        """Calculate urgency score for breaking news detection"""
        text = f"{title} {summary}".lower()
        score = 0.0
        
        # Check breaking news keywords
        for keyword in self.breaking_keywords:
            if keyword.lower() in text:
                if keyword in ['breaking', 'urgent', 'alerte', 'exclusif']:
                    score += 3.0  # High urgency
                elif keyword in ['dernière minute', 'état d\'urgence']:
                    score += 2.5  # Very high urgency
                elif keyword in ['gouvernement', 'président', 'crise']:
                    score += 2.0  # High importance
                else:
                    score += 1.0  # Medium importance
        
        # Check for time-sensitive language
        urgent_patterns = [
            r'\b(?:maintenant|immédiatement|urgent|breaking)\b',
            r'\b(?:en cours|actuellement|ce matin)\b',
            r'\b(?:annonce|révèle|confirme)\b'
        ]
        
        for pattern in urgent_patterns:
            if re.search(pattern, text):
                score += 0.5
        
        return min(score, 10.0)  # Cap at 10.0
    
    def parse_feed_entry(self, entry, source_name: str, feed_url: str) -> NewsArticle:
        """Parse a single RSS feed entry into NewsArticle (enhanced from manual system)"""
        
        # Extract basic info
        title = self.clean_text(entry.get('title', ''))
        summary = self.clean_text(entry.get('summary', '') or entry.get('description', ''))
        link = entry.get('link', '')
        
        # Handle publication date
        published = entry.get('published', '')
        published_parsed = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_parsed = datetime(*entry.published_parsed[:6]).isoformat()
            except:
                published_parsed = None
        
        # Extract author
        author = None
        if hasattr(entry, 'author'):
            author = self.clean_text(entry.author)
        elif hasattr(entry, 'authors') and entry.authors:
            author = self.clean_text(entry.authors[0].get('name', ''))
        
        # Extract category/tags
        category = None
        tags = []
        if hasattr(entry, 'category'):
            category = self.clean_text(entry.category)
        
        if hasattr(entry, 'tags') and entry.tags:
            tags = [self.clean_text(tag.get('term', '')) for tag in entry.tags]
        
        # Extract content
        content = None
        if hasattr(entry, 'content') and entry.content:
            content = self.clean_text(entry.content[0].get('value', ''))
        elif hasattr(entry, 'summary_detail'):
            content = self.clean_text(entry.summary_detail.get('value', ''))
        
        # Extract image
        image_url, image_title = self.extract_image_from_entry(entry)
        
        # Generate unique hash
        hash_content = f"{title}_{link}_{published}_{source_name}"
        article_hash = hashlib.md5(hash_content.encode()).hexdigest()
        
        # Calculate urgency score for breaking news
        urgency_score = self.calculate_urgency_score(title, summary)
        is_breaking = urgency_score >= 3.0
        
        # Current timestamp
        scraped_at = datetime.now(timezone.utc).isoformat()
        
        return NewsArticle(
            title=title,
            summary=summary,
            link=link,
            published=published,
            published_parsed=published_parsed,
            source_name=source_name,
            source_url=urlparse(link).netloc if link else "",
            feed_url=feed_url,
            author=author,
            category=category,
            tags=tags,
            content=content,
            image_url=image_url,
            image_title=image_title,
            guid=entry.get('id', entry.get('guid', '')),
            language=entry.get('language', 'fr'),
            scraped_at=scraped_at,
            article_hash=article_hash,
            content_hash=self.create_content_hash(title, summary, content),
            breaking_news=is_breaking,
            urgency_score=urgency_score
        )
    
    def is_article_cached(self, article_hash: str, max_age_hours: int = 24) -> bool:
        """Check if article is already in cache and still fresh"""
        with self.scraping_lock:
            if article_hash not in self.deduplicator.article_cache:
                return False
            
            cached_time = self.deduplicator.article_cache[article_hash].get('cached_at')
            if not cached_time:
                return False
            
            cache_age = datetime.now(timezone.utc) - datetime.fromisoformat(cached_time)
            return cache_age < timedelta(hours=max_age_hours)
    
    def cache_article(self, article: NewsArticle):
        """Cache article for smart deduplication"""
        with self.scraping_lock:
            self.deduplicator.add_article(article)
    
    def scrape_single_feed(self, source_name: str, feed_url: str, 
                          breaking_news_only: bool = False, scan_type: str = "regular") -> List[NewsArticle]:
        """Enhanced scraping with deduplication and intelligent limits"""
        if source_name in self.failed_sources:
            logger.debug(f"⏭️ Skipping failed source: {source_name}")
            return []
        
        articles = []
        
        # Determine article limit per source
        if scan_type == "breaking":
            max_per_source = self.scraping_config['max_articles_per_source_breaking']
        else:
            max_per_source = self.scraping_config['max_articles_per_source_regular']
        
        try:
            logger.debug(f"📡 Scraping {source_name}: {feed_url} (max: {max_per_source})")
            
            # Get the feed with timeout
            timeout = self.scraping_config['request_timeout_seconds']
            response = self.session.get(feed_url, timeout=timeout)
            response.raise_for_status()
            
            # Parse the feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"⚠️ Feed parsing issues for {source_name}: {feed.bozo_exception}")
            
            # Track source reliability
            self.source_reliability[source_name] = self.source_reliability.get(source_name, 0) + 1
            self.source_last_success[source_name] = datetime.now(timezone.utc).isoformat()
            
            # Get appropriate time filter
            time_cutoff = self.get_time_filter(scan_type)
            
            # Process entries with intelligent limits
            processed_count = 0
            for entry in feed.entries:
                if processed_count >= max_per_source:
                    logger.debug(f"📊 {source_name}: Reached per-source limit ({max_per_source})")
                    break
                
                try:
                    article = self.parse_feed_entry(entry, source_name, feed_url)
                    
                    # Check for duplicates first (most important check)
                    is_duplicate, original_hash = self.deduplicator.is_duplicate(article)
                    if is_duplicate:
                        logger.debug(f"🔄 Duplicate detected: {article.title[:30]}... (original: {original_hash[:8]})")
                        continue
                    
                    # Time filtering
                    include_article = True
                    if article.published_parsed:
                        try:
                            article_date = date_parser.parse(article.published_parsed)
                            if article_date.tzinfo is None:
                                article_date = article_date.replace(tzinfo=timezone.utc)
                            
                            if article_date < time_cutoff:
                                include_article = False
                                logger.debug(f"⏰ Article too old: {article.title[:30]}...")
                        except:
                            pass  # Include if date parsing fails
                    
                    # Breaking news filtering
                    if breaking_news_only and not article.breaking_news:
                        include_article = False
                    
                    if include_article:
                        # Add to deduplication cache
                        self.deduplicator.add_article(article, scan_type)
                        articles.append(article)
                        processed_count += 1
                        
                        if article.breaking_news:
                            logger.info(f"🚨 Breaking news: {article.title[:50]}...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing entry from {source_name}: {e}")
                    continue
            
            logger.debug(f"✅ {source_name}: {len(articles)} articles collected")
            
        except requests.RequestException as e:
            logger.warning(f"❌ Request failed for {source_name}: {e}")
            self.source_reliability[source_name] = self.source_reliability.get(source_name, 0) - 2
            
            # Mark as failed if reliability drops too low
            if self.source_reliability.get(source_name, 0) < -5:
                self.failed_sources.add(source_name)
                logger.warning(f"🚫 Marking {source_name} as unreliable")
                
        except Exception as e:
            logger.error(f"❌ Unexpected error scraping {source_name}: {e}")
        
        return articles
    
    def quick_breaking_news_scan(self, breaking_keywords: List[str]) -> List[NewsArticle]:
        """Enhanced breaking news scan with deduplication"""
        logger.info("🔥 Enhanced breaking news scan with deduplication...")
        
        # Focus on most reliable breaking news sources
        priority_sources = {
            source: self.feed_urls[source] 
            for source in self.scraping_config['breaking_news_priority_sources']
            if source in self.feed_urls
        }
        
        all_articles = []
        scan_start_time = time.time()
        
        # Clean up old cache entries before scanning
        self.deduplicator.cleanup_old_cache()
        
        with ThreadPoolExecutor(max_workers=min(5, len(priority_sources))) as executor:
            future_to_source = {
                executor.submit(self.scrape_single_feed, source, url, True, "breaking"): source 
                for source, url in priority_sources.items()
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    logger.debug(f"📰 {source}: {len(articles)} breaking news articles")
                except Exception as e:
                    logger.warning(f"⚠️ Breaking news scan failed for {source}: {e}")
        
        # Apply intelligent limits and prioritization
        limited_articles = self.apply_article_limits(all_articles, "breaking")
        
        # Final filtering for highest urgency
        breaking_articles = [a for a in limited_articles if a.urgency_score >= 2.0]
        
        scan_duration = time.time() - scan_start_time
        logger.info(f"🚨 Breaking news scan complete: {len(breaking_articles)}/{len(all_articles)} articles selected in {scan_duration:.2f}s")
        
        # Log deduplication stats
        total_cache_size = len(self.deduplicator.article_cache)
        logger.debug(f"📊 Deduplication cache size: {total_cache_size} articles")
        
        return breaking_articles
    
    def comprehensive_scrape(self) -> List[NewsArticle]:
        """Enhanced comprehensive scraping with smart deduplication and limits"""
        logger.info("🔄 Enhanced comprehensive scraping with deduplication...")
        
        all_articles = []
        scrape_start_time = time.time()
        failed_sources_count = 0
        
        # Clean up old cache entries before major scraping
        self.deduplicator.cleanup_old_cache()
        
        # Get all active sources (excluding failed ones)
        active_sources = {
            source: url for source, url in self.feed_urls.items() 
            if source not in self.failed_sources
        }
        
        logger.info(f"📡 Scraping {len(active_sources)} active sources (excluded {len(self.failed_sources)} failed)")
        
        max_workers = min(self.scraping_config['parallel_scraping_threads'], len(active_sources))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_source = {
                executor.submit(self.scrape_single_feed, source, url, False, "regular"): source 
                for source, url in active_sources.items()
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    logger.debug(f"📰 {source}: {len(articles)} articles collected")
                except Exception as e:
                    logger.error(f"❌ Comprehensive scrape failed for {source}: {e}")
                    failed_sources_count += 1
        
        # Apply intelligent limits and prioritization
        limited_articles = self.apply_article_limits(all_articles, "regular")
        
        # Sort final results by urgency and source priority
        final_articles = sorted(limited_articles, key=lambda x: (
            x.urgency_score,
            self.deduplicator._get_source_priority(x.source_name),
            x.published_parsed or "1970-01-01"
        ), reverse=True)
        
        scrape_duration = time.time() - scrape_start_time
        breaking_count = len([a for a in final_articles if a.breaking_news])
        
        logger.info(f"📊 Comprehensive scrape complete in {scrape_duration:.2f}s:")
        logger.info(f"   📄 Total articles: {len(final_articles)} (from {len(all_articles)} raw)")
        logger.info(f"   🚨 Breaking news: {breaking_count}")
        logger.info(f"   ❌ Failed sources: {failed_sources_count}")
        logger.info(f"   🔄 Duplicates filtered: {len(all_articles) - len(limited_articles)}")
        logger.info(f"   📊 Cache size: {len(self.deduplicator.article_cache)}")
        
        return final_articles
    
    def save_articles(self, articles: List[NewsArticle], filename_prefix: str = "scraped") -> str:
        """Save articles to JSON file in website-compatible format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to data directory with timestamp
        data_filename = f"../data/live/{filename_prefix}_{timestamp}.json"
        
        # Save to website directory as current_articles.json
        website_filename = f"../website/current_articles.json"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(data_filename), exist_ok=True)
        os.makedirs(os.path.dirname(website_filename), exist_ok=True)
        
        # Convert NewsArticle objects to website-compatible format
        compatible_articles = []
        for article in articles:
            # Convert our NewsArticle format to website-expected format
            compatible_article = {
                "title": article.title,
                "summary": article.summary,
                "link": article.link,
                "source_name": article.source_name,
                "published": article.published,
                "author": article.author,
                "image_url": article.image_url,
                
                # Add compatibility fields for website
                "quality_score": 7.0,  # Default quality score
                "relevance_score": 6.0,  # Default relevance score  
                "importance_score": 7.0,  # Default importance score
                "total_score": 20.0,  # Sum of above scores
                "breaking_news": article.breaking_news,
                "urgency_score": article.urgency_score,
                "fast_tracked": False,
                "curated_at": article.scraped_at,
                "curation_id": article.article_hash[:8],  # Use first 8 chars of hash
                "added_at": article.scraped_at
            }
            compatible_articles.append(compatible_article)
        
        # Prepare data in website-compatible format
        website_data = {
            "metadata": {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "total_articles": len(articles),
                "automation_system": "Better French Max Automated System",
                "website_version": "1.0",
                "curated_articles_count": len(articles),
                "update_type": "automated_scraping",
                "average_score": 20.0,  # Default average
                "breaking_news_count": len([a for a in articles if a.breaking_news]),
                "sources_scraped": len(set(a.source_name for a in articles)),
                "scraper_version": "Smart Scraper 1.0"
            },
            "articles": compatible_articles
        }
        
        # Save to both locations
        with open(website_filename, 'w', encoding='utf-8') as f:
            json.dump(website_data, f, ensure_ascii=False, indent=2)
        
        with open(data_filename, 'w', encoding='utf-8') as f:
            json.dump(website_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Articles saved to website: {website_filename}")
        logger.info(f"💾 Articles archived to: {data_filename}")
        
        return website_filename
    
    def get_source_reliability_report(self) -> Dict[str, Any]:
        """Get source reliability and performance metrics"""
        return {
            "reliable_sources": {k: v for k, v in self.source_reliability.items() if v > 0},
            "failed_sources": list(self.failed_sources),
            "cache_size": len(self.deduplicator.article_cache),
            "total_sources_configured": len(self.feed_urls)
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get detailed processing and deduplication statistics"""
        with self.scraping_lock:
            cache_stats = {}
            processing_stages = {}
            
            for cache_hash, metadata in self.deduplicator.article_cache.items():
                for stage in metadata.processing_history:
                    processing_stages[stage] = processing_stages.get(stage, 0) + 1
            
            return {
                "scraping_stats": {
                    "total_sources_configured": len(self.feed_urls),
                    "active_sources": len(self.feed_urls) - len(self.failed_sources),
                    "failed_sources": list(self.failed_sources),
                    "source_reliability_scores": self.source_reliability.copy()
                },
                "deduplication_stats": {
                    "cache_size": len(self.deduplicator.article_cache),
                    "similarity_cache_size": len(self.deduplicator.similarity_cache),
                    "processing_stages": processing_stages
                },
                "configuration": {
                    "breaking_timeframe_hours": self.scraping_config['breaking_news_timeframe_hours'],
                    "regular_timeframe_hours": self.scraping_config['regular_update_timeframe_hours'],
                    "max_breaking_articles": self.scraping_config['max_total_articles_breaking'],
                    "max_regular_articles": self.scraping_config['max_total_articles_regular'],
                    "deduplication_enabled": self.scraping_config['enable_duplicate_detection']
                }
            }

# Test function for development
def test_smart_scraper():
    """Test the smart scraper functionality"""
    print("🧪 Testing Smart Scraper...")
    
    scraper = SmartScraper()
    
    # Test breaking news scan
    breaking_articles = scraper.quick_breaking_news_scan([])
    print(f"📰 Breaking news test: {len(breaking_articles)} articles")
    
    # Test single source
    test_articles = scraper.scrape_single_feed("France Info", scraper.feed_urls["France Info"])
    print(f"📺 France Info test: {len(test_articles)} articles")
    
    if test_articles:
        print(f"🔍 Sample article: {test_articles[0].title[:50]}...")
        print(f"🚨 Breaking: {test_articles[0].breaking_news}")
        print(f"⚡ Urgency: {test_articles[0].urgency_score}")
    
    print("✅ Smart Scraper test completed")

if __name__ == "__main__":
    test_smart_scraper() 