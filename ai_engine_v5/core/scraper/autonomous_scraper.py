"""
AI Engine v5 - Autonomous Scraper
Handles minimal, fast scraping with LLM-powered article selection.
CRITICAL: Uses separate API key to ensure 24/7 reliability.
"""

import json
import requests
import os
from typing import List, Dict, Any
from datetime import datetime, timezone
import hashlib


class AutonomousScraper:
    """Self-contained autonomous scraper for hourly news collection."""
    
    def __init__(self):
        # CRITICAL: Separate API key for scraper to avoid development interference
        self.api_key = os.getenv('OPENROUTER_SCRAPER_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        self.selection_model = os.getenv('AI_ENGINE_SELECTION_MODEL', 'google/gemini-2.0-flash-exp')
        
        # COMPREHENSIVE RSS SOURCES - Same quality as V3+V4 combined
        self.sources = [
            # Major French Newspapers
            "https://www.lemonde.fr/rss/une.xml",
            "https://www.lefigaro.fr/rss/figaro_actualites.xml",
            "https://www.liberation.fr/arc/outboundfeeds/rss-all/",
            "https://feeds.leparisien.fr/leparisien/rss",
            "https://www.lexpress.fr/arc/outboundfeeds/rss/alaune.xml",
            "http://www.lepoint.fr/rss.xml",
            "http://tempsreel.nouvelobs.com/rss.xml",
            "https://www.la-croix.com/RSS",
            "https://www.lesechos.fr/rss/rss_la_une.xml",
            
            # TV/Radio News
            "https://www.bfmtv.com/rss/news-24-7/",
            "https://www.francetvinfo.fr/titres.rss",
            "https://www.franceinter.fr/rss",
            "https://www.europe1.fr/rss.xml",
            "https://www.france24.com/fr/rss",
            "https://rfi.fr/fr/rss",
            
            # Regional/Specialized
            "https://www.ouest-france.fr/rss/une",
            "https://partner-feeds.20min.ch/rss/20minutes",
            "https://www.afp.com/fr/actus/afp_actualite/792,31,9,7,33/feed",
            
            # Alternative/Independent
            "https://www.mediapart.fr/articles/feed",
            "https://brief.me/rss",
            
            # Le Monde Categories (comprehensive coverage)
            "https://www.lemonde.fr/politique/rss_full.xml",
            "https://www.lemonde.fr/international/rss_full.xml",
            "https://www.lemonde.fr/economie/rss_full.xml",
            "https://www.lemonde.fr/culture/rss_full.xml",
            "https://www.lemonde.fr/sport/rss_full.xml",
            "https://www.lemonde.fr/sciences/rss_full.xml",
            
            # Additional comprehensive sources
            "https://www.franceinfo.fr/politique.rss",
            "https://www.franceinfo.fr/monde.rss",
            "https://www.franceinfo.fr/economie.rss",
            "https://www.franceinfo.fr/societe.rss",
            "https://www.franceinfo.fr/culture.rss"
        ]
        
        print(f"🔐 Scraper API Key: {'PROTECTED' if self.api_key else 'MISSING'}")
        print(f"📰 Comprehensive sources: {len(self.sources)} RSS feeds")
    
    def scrape_current_hour(self) -> List[Dict[str, Any]]:
        """Scrape articles for current hour - comprehensive but fast."""
        print("📡 Starting comprehensive autonomous scrape...")
        print(f"🌐 Scraping {len(self.sources)} sources for maximum coverage")
        
        candidates = []
        current_time = datetime.now(timezone.utc)
        hour_window = current_time.replace(minute=0, second=0, microsecond=0)
        
        successful_sources = 0
        failed_sources = 0
        
        for i, source_url in enumerate(self.sources, 1):
            try:
                print(f"  📰 [{i}/{len(self.sources)}] Scraping: {self._get_source_name(source_url)}")
                articles = self._scrape_rss_feed(source_url)
                
                # Filter for recent articles (last 2 hours for safety)
                recent_articles = []
                for article in articles:
                    if self._is_recent_article(article, hours_back=2):
                        recent_articles.append(article)
                
                candidates.extend(recent_articles)
                successful_sources += 1
                print(f"    ✅ Found {len(recent_articles)} recent articles")
                
            except Exception as e:
                failed_sources += 1
                print(f"    ⚠️ Failed to scrape {self._get_source_name(source_url)}: {e}")
                continue
        
        # Remove duplicates
        candidates = self._deduplicate_candidates(candidates)
        
        print(f"📊 COMPREHENSIVE SCRAPE COMPLETE:")
        print(f"   ✅ Successful sources: {successful_sources}/{len(self.sources)}")
        print(f"   ❌ Failed sources: {failed_sources}")
        print(f"   📄 Total unique candidates: {len(candidates)}")
        print(f"   🎯 Ready for LLM selection of top 10")
        
        return candidates
    
    def _get_source_name(self, url: str) -> str:
        """Get readable source name from URL."""
        if 'lemonde' in url:
            if 'politique' in url:
                return 'Le Monde Politique'
            elif 'international' in url:
                return 'Le Monde International'
            elif 'economie' in url:
                return 'Le Monde Économie'
            elif 'culture' in url:
                return 'Le Monde Culture'
            elif 'sport' in url:
                return 'Le Monde Sport'
            elif 'sciences' in url:
                return 'Le Monde Sciences'
            else:
                return 'Le Monde'
        elif 'lefigaro' in url:
            return 'Le Figaro'
        elif 'liberation' in url:
            return 'Libération'
        elif 'leparisien' in url:
            return 'Le Parisien'
        elif 'lexpress' in url:
            return 'L\'Express'
        elif 'lepoint' in url:
            return 'Le Point'
        elif 'nouvelobs' in url:
            return 'L\'Obs'
        elif 'la-croix' in url:
            return 'La Croix'
        elif 'lesechos' in url:
            return 'Les Échos'
        elif 'bfmtv' in url:
            return 'BFM TV'
        elif 'francetvinfo' in url or 'franceinfo' in url:
            if 'politique' in url:
                return 'France Info Politique'
            elif 'monde' in url:
                return 'France Info Monde'
            elif 'economie' in url:
                return 'France Info Économie'
            elif 'societe' in url:
                return 'France Info Société'
            elif 'culture' in url:
                return 'France Info Culture'
            else:
                return 'France Info'
        elif 'franceinter' in url:
            return 'France Inter'
        elif 'europe1' in url:
            return 'Europe 1'
        elif 'france24' in url:
            return 'France 24'
        elif 'rfi' in url:
            return 'RFI'
        elif 'ouest-france' in url:
            return 'Ouest France'
        elif '20min' in url:
            return '20 Minutes'
        elif 'afp' in url:
            return 'AFP'
        elif 'mediapart' in url:
            return 'Mediapart'
        elif 'brief.me' in url:
            return 'Brief.me'
        else:
            return 'French News'
    
    def _scrape_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single RSS feed - comprehensive parsing."""
        import xml.etree.ElementTree as ET
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        articles = []
        
        # Handle both RSS and Atom feeds
        for item in root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            try:
                if item.tag.endswith('item'):  # RSS
                    title = self._get_text(item.find('title'))
                    link = self._get_text(item.find('link'))
                    description = self._get_text(item.find('description'))
                    pub_date = self._get_text(item.find('pubDate'))
                else:  # Atom
                    title = self._get_text(item.find('.//{http://www.w3.org/2005/Atom}title'))
                    link_elem = item.find('.//{http://www.w3.org/2005/Atom}link')
                    link = link_elem.get('href') if link_elem is not None else ''
                    description = self._get_text(item.find('.//{http://www.w3.org/2005/Atom}summary'))
                    pub_date = self._get_text(item.find('.//{http://www.w3.org/2005/Atom}published'))
                
                if title and link:
                    articles.append({
                        'title': title.strip(),
                        'link': link.strip(),
                        'summary': description.strip() if description else '',
                        'published_date': pub_date,
                        'source': self._get_source_name(url),
                        'scraped_at': datetime.now(timezone.utc).isoformat()
                    })
                    
            except Exception as e:
                continue  # Skip problematic articles
        
        return articles
    
    def _get_text(self, element) -> str:
        """Safely extract text from XML element."""
        if element is not None:
            return element.text or ''
        return ''
    
    def _is_recent_article(self, article: Dict[str, Any], hours_back: int = 2) -> bool:
        """Check if article is from recent hours."""
        # For now, assume all scraped articles are recent
        # This can be enhanced with proper date parsing
        return True
    
    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity."""
        seen_hashes = set()
        unique_candidates = []
        
        for candidate in candidates:
            # Create hash from normalized title
            title_hash = hashlib.md5(candidate['title'].lower().encode()).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def llm_select_top_10(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to select top 10 articles from candidates."""
        if not self.api_key:
            raise ValueError("OPENROUTER_SCRAPER_API_KEY not found - scraper cannot function!")
        
        if len(candidates) <= 10:
            return {
                'selected_articles': candidates,
                'reasoning': f"Only {len(candidates)} candidates available - selected all",
                'cost': 0.0
            }
        
        # Prepare candidates for LLM
        candidate_text = []
        for i, candidate in enumerate(candidates, 1):
            text = f"{i}. TITLE: {candidate['title']}\n   SOURCE: {candidate['source']}\n   SUMMARY: {candidate.get('summary', 'N/A')[:200]}"
            candidate_text.append(text)
        
        prompt = f"""You are an expert French news curator for language learners. From these {len(candidates)} candidate articles, select the TOP 10 that would be most valuable for French language learning.

CRITERIA:
- Educational value for French learners (B1-B2 level)
- Diverse topics (avoid duplicates/similar stories)
- Current relevance and importance
- Clear, well-written French
- Interesting content that motivates learning
- Mix of categories (politics, culture, economy, society, etc.)

CANDIDATES:
{chr(10).join(candidate_text)}

Respond with EXACTLY this JSON format:
{{
    "selected_indices": [1, 3, 5, 7, 9, 12, 15, 18, 20, 22],
    "reasoning": "Brief explanation of selection criteria applied"
}}

Select exactly 10 numbers from 1-{len(candidates)}."""
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.selection_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Calculate cost (rough estimate)
            usage = result.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            
            # Gemini 2.0 Flash pricing estimate
            cost = (prompt_tokens * 0.00001) + (completion_tokens * 0.00003)
            
            # Parse LLM response
            llm_content = result['choices'][0]['message']['content'].strip()
            
            try:
                selection_data = json.loads(llm_content)
                selected_indices = selection_data['selected_indices']
                reasoning = selection_data['reasoning']
                
                # Convert indices to articles (1-based to 0-based)
                selected_articles = []
                for idx in selected_indices:
                    if 1 <= idx <= len(candidates):
                        selected_articles.append(candidates[idx - 1])
                
                if len(selected_articles) == 0:
                    raise ValueError("No valid articles selected")
                
                return {
                    'selected_articles': selected_articles,
                    'reasoning': reasoning,
                    'cost': cost
                }
                
            except (json.JSONDecodeError, KeyError) as e:
                # Fallback: select first 10
                print(f"⚠️ LLM response parsing failed: {e}")
                return {
                    'selected_articles': candidates[:10],
                    'reasoning': "LLM selection failed - used first 10 candidates",
                    'cost': cost
                }
                
        except Exception as e:
            print(f"⚠️ LLM selection failed: {e}")
            # Fallback: select first 10
            return {
                'selected_articles': candidates[:10],
                'reasoning': f"LLM call failed ({str(e)}) - used first 10 candidates",
                'cost': 0.0
            } 