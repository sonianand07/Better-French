"""
AI Engine v5 - Autonomous Scraper
Handles minimal, fast scraping with LLM-powered article selection.
CRITICAL: Uses separate API key to ensure 24/7 reliability.
"""

import json
import requests
import os
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone, timedelta
import hashlib
import asyncio
import aiohttp
import feedparser
import logging
from dataclasses import dataclass, asdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.rss_sources import RSS_SOURCES

logger = logging.getLogger(__name__)

@dataclass
class ArticleData:
    title: str
    link: str
    summary: str
    published: str
    source: str
    hash_id: str
    raw_content: str = ""

@dataclass  
class UserProfile:
    """Profile data for personalized article selection"""
    user_id: str = "default"
    native_lang: str = "en"
    french_level: str = "B1"
    lives_in: str = ""
    work_domains: List[str] = None
    pain_points: List[str] = None
    interests: List[str] = None
    
    def __post_init__(self):
        if self.work_domains is None:
            self.work_domains = []
        if self.pain_points is None:
            self.pain_points = []
        if self.interests is None:
            self.interests = []
    
    @classmethod
    def from_json(cls, profile_data: Dict) -> 'UserProfile':
        return cls(**profile_data)
    
    def get_keywords(self) -> Set[str]:
        """Get all profile keywords for relevance scoring"""
        keywords = set()
        keywords.update(kw.lower() for kw in self.work_domains)
        keywords.update(kw.lower() for kw in self.pain_points)
        keywords.update(kw.lower() for kw in self.interests)
        if self.lives_in:
            keywords.add(self.lives_in.lower())
        return keywords

class AutonomousScraper:
    """Rony - The autonomous French news scraper
    
    Scrapes 31 RSS sources and uses Gemini 2.5 Flash to select
    the top 10 articles based on profile preferences.
    """
    
    def __init__(self, api_key: str, profile: Optional[UserProfile] = None):
        self.api_key = api_key
        self.profile = profile or UserProfile()  # Default profile if none provided
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_hash(self, title: str, link: str) -> str:
        """Generate unique hash for article deduplication"""
        content = f"{title}{link}".encode('utf-8')
        return hashlib.md5(content).hexdigest()[:12]
    
    async def _fetch_rss_feed(self, source_name: str, url: str) -> List[ArticleData]:
        """Fetch and parse a single RSS feed"""
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {source_name}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries[:10]:  # Limit per source
                    article = ArticleData(
                        title=entry.get('title', ''),
                        link=entry.get('link', ''),
                        summary=entry.get('summary', entry.get('description', '')),
                        published=entry.get('published', ''),
                        source=source_name,
                        hash_id=self._generate_hash(entry.get('title', ''), entry.get('link', ''))
                    )
                    articles.append(article)
                
                logger.info(f"Fetched {len(articles)} articles from {source_name}")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")
            return []
    
    async def scrape_all_sources(self) -> List[ArticleData]:
        """Scrape all RSS sources concurrently"""
        logger.info(f"Rony starting scrape of {len(RSS_SOURCES)} sources...")
        
        tasks = []
        for source_name, url in RSS_SOURCES.items():
            task = self._fetch_rss_feed(source_name, url)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Feed fetch failed: {result}")
        
        # Deduplicate by hash_id
        seen_hashes = set()
        unique_articles = []
        for article in all_articles:
            if article.hash_id not in seen_hashes:
                seen_hashes.add(article.hash_id)
                unique_articles.append(article)
        
        logger.info(f"Rony collected {len(unique_articles)} unique articles from {len(RSS_SOURCES)} sources")
        return unique_articles
    
    async def _select_best_articles(self, articles: List[ArticleData]) -> List[ArticleData]:
        """Use Gemini 2.5 Flash to intelligently select top 10 articles based on profile"""
        
        if not articles:
            return []
        
        # Create profile context for LLM
        profile_context = f"""
USER PROFILE:
- French Level: {self.profile.french_level}
- Lives in: {self.profile.lives_in or 'France'}
- Work Domains: {', '.join(self.profile.work_domains) if self.profile.work_domains else 'General'}
- Pain Points: {', '.join(self.profile.pain_points) if self.profile.pain_points else 'None specified'}
- Interests: {', '.join(self.profile.interests) if self.profile.interests else 'General news'}
        """
        
        # Prepare article summaries for LLM
        article_summaries = []
        for i, article in enumerate(articles):
            summary = f"{i+1}. {article.title}\n   Source: {article.source}\n   Summary: {article.summary[:200]}..."
            article_summaries.append(summary)
        
        prompt = f"""You are Rony, an intelligent French news curator for French language learners.

{profile_context}

Below are {len(articles)} French news articles. Select the TOP 10 most relevant articles for this user profile.

Consider:
1. Relevance to user's work domains, pain points, and interests
2. Practical value for someone living in France  
3. Language learning value (interesting but not too complex for {self.profile.french_level} level)
4. News diversity (avoid 5 articles about same topic)
5. Priority for articles about user's location ({self.profile.lives_in or 'France'})

ARTICLES:
{chr(10).join(article_summaries)}

Respond with ONLY the numbers of the 10 best articles, separated by commas.
Example: 1,3,7,12,15,18,22,25,28,30"""

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'google/gemini-2.0-flash-exp:free',
                'messages': [
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                'max_tokens': 50,
                'temperature': 0.3
            }
            
            async with self.session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    logger.error(f"Gemini API error: {response.status}")
                    # Fallback: return first 10 articles
                    return articles[:10]
                
                result = await response.json()
                selected_text = result['choices'][0]['message']['content'].strip()
                
                # Parse selected indices
                try:
                    selected_indices = [int(x.strip()) - 1 for x in selected_text.split(',')]
                    selected_articles = [articles[i] for i in selected_indices if 0 <= i < len(articles)]
                    
                    if len(selected_articles) < 10:
                        # Fill up to 10 if not enough selected
                        remaining = [a for a in articles if a not in selected_articles]
                        selected_articles.extend(remaining[:10 - len(selected_articles)])
                    
                    logger.info(f"Rony intelligently selected {len(selected_articles)} articles using profile-aware curation")
                    return selected_articles[:10]
                    
                except (ValueError, IndexError) as e:
                    logger.error(f"Failed to parse Gemini selection: {e}")
                    return articles[:10]
                    
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return articles[:10]  # Fallback
    
    async def run_autonomous_cycle(self) -> Dict:
        """Complete autonomous scraping and selection cycle"""
        start_time = datetime.now()
        
        # Step 1: Scrape all sources
        all_articles = await self.scrape_all_sources()
        
        if not all_articles:
            logger.warning("No articles collected!")
            return {
                "timestamp": start_time.isoformat(),
                "articles_collected": 0,
                "articles_selected": 0,
                "selected_articles": [],
                "profile_used": asdict(self.profile)
            }
        
        # Step 2: Intelligent selection using profile
        selected_articles = await self._select_best_articles(all_articles)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Rony completed autonomous cycle in {duration:.1f}s: {len(all_articles)} → {len(selected_articles)} articles")
        
        return {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "articles_collected": len(all_articles),
            "articles_selected": len(selected_articles),
            "selected_articles": [asdict(article) for article in selected_articles],
            "profile_used": asdict(self.profile),
            "sources_scraped": list(RSS_SOURCES.keys())
        }

# Convenience function for single-use
async def run_autonomous_scraper(api_key: str, profile_data: Optional[Dict] = None) -> Dict:
    """Run Rony's autonomous scraping cycle with optional profile"""
    profile = None
    if profile_data:
        profile = UserProfile.from_json(profile_data)
    
    async with AutonomousScraper(api_key, profile) as scraper:
        return await scraper.run_autonomous_cycle() 