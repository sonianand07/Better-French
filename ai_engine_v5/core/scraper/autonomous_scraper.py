"""
AI Engine v5 - Autonomous Scraper
Handles minimal, fast scraping with LLM-powered article selection.
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
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.selection_model = os.getenv('AI_ENGINE_SELECTION_MODEL', 'google/gemini-2.0-flash-exp')
        self.sources = [
            "https://www.lemonde.fr/rss/une.xml",
            "https://www.lefigaro.fr/rss/figaro_une.xml", 
            "https://feeds.leparisien.fr/leparisien/une",
            "https://www.francetvinfo.fr/titres.rss",
            "https://www.liberation.fr/arc/outboundfeeds/rss-all/",
            "https://www.europe1.fr/rss.xml",
            "https://www.franceinter.fr/rss/a-la-une.xml"
        ]
    
    def scrape_current_hour(self) -> List[Dict[str, Any]]:
        """Scrape articles for current hour - minimal and fast."""
        print("📡 Starting autonomous scrape...")
        
        candidates = []
        current_time = datetime.now(timezone.utc)
        hour_window = current_time.replace(minute=0, second=0, microsecond=0)
        
        for source_url in self.sources:
            try:
                print(f"  📰 Scraping: {source_url}")
                articles = self._scrape_rss_feed(source_url)
                
                # Filter for recent articles (last 2 hours for safety)
                recent_articles = []
                for article in articles:
                    if self._is_recent_article(article, hours_back=2):
                        recent_articles.append(article)
                
                candidates.extend(recent_articles)
                print(f"    ✅ Found {len(recent_articles)} recent articles")
                
            except Exception as e:
                print(f"    ⚠️ Failed to scrape {source_url}: {e}")
                continue
        
        # Remove duplicates
        candidates = self._deduplicate_candidates(candidates)
        
        print(f"📊 Total unique candidates: {len(candidates)}")
        return candidates
    
    def _scrape_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single RSS feed - simplified."""
        import xml.etree.ElementTree as ET
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
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
                        'source': self._extract_source_name(url),
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
    
    def _extract_source_name(self, url: str) -> str:
        """Extract source name from URL."""
        if 'lemonde' in url:
            return 'Le Monde'
        elif 'lefigaro' in url:
            return 'Le Figaro'
        elif 'leparisien' in url:
            return 'Le Parisien'
        elif 'francetvinfo' in url:
            return 'France TV Info'
        elif 'liberation' in url:
            return 'Libération'
        elif 'europe1' in url:
            return 'Europe 1'
        elif 'franceinter' in url:
            return 'France Inter'
        else:
            return 'French News'
    
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
            # Create hash from title (simple deduplication)
            title_hash = hashlib.md5(candidate['title'].lower().encode()).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def llm_select_top_10(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to select top 10 articles from candidates."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")
        
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
- Educational value for French learners
- Diverse topics (avoid duplicates)
- Current relevance
- Clear, well-written French
- Interesting content that motivates learning

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