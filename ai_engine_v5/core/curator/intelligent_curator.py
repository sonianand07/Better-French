#!/usr/bin/env python3
"""
AI Engine v5 - Intelligent Curator
Simplified version that works with the autonomous scraper approach.
This is mainly for future enhancements - current selection is done by LLM in scraper.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib


@dataclass
class Article:
    """Simple article data structure for v5."""
    title: str
    summary: str
    link: str
    source: str
    published_date: str
    content: Optional[str] = ""


@dataclass 
class CurationResult:
    """Result of intelligent curation process."""
    selected_articles: List[Article]
    rejected_count: int
    diversity_score: float
    avg_quality: float
    topic_distribution: Dict[str, int]


class IntelligentCurator:
    """
    Simplified intelligent curator for v5.
    
    In v5, most curation is done by the LLM in the autonomous scraper.
    This class provides utilities for future semantic enhancements.
    """
    
    def __init__(self):
        self.similarity_threshold = 0.8
        
    def curate_articles(
        self, 
        candidates: List[Article], 
        existing_articles: Optional[List[Article]] = None
    ) -> CurationResult:
        """
        Basic curation for v5 - mainly deduplication.
        Advanced semantic curation will be added later.
        """
        if not candidates:
            return CurationResult(
                selected_articles=[],
                rejected_count=0,
                diversity_score=0.0,
                avg_quality=0.0,
                topic_distribution={}
            )
        
        # Simple deduplication based on title similarity
        deduplicated = self._remove_duplicates(candidates)
        
        # For now, select up to 10 articles (this is mainly done by LLM in scraper)
        selected = deduplicated[:10]
        
        # Calculate basic metrics
        diversity_score = self._calculate_diversity(selected)
        avg_quality = 0.75  # Placeholder - will be enhanced with actual quality metrics
        topic_dist = self._analyze_topic_distribution(selected)
        
        return CurationResult(
            selected_articles=selected,
            rejected_count=len(candidates) - len(selected),
            diversity_score=diversity_score,
            avg_quality=avg_quality,
            topic_distribution=topic_dist
        )
    
    def _remove_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate articles based on title similarity."""
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            # Create hash from normalized title
            title_hash = hashlib.md5(
                article.title.lower().strip().encode('utf-8')
            ).hexdigest()
            
            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique_articles.append(article)
        
        return unique_articles
    
    def _calculate_diversity(self, articles: List[Article]) -> float:
        """Calculate topic diversity score (simplified)."""
        if not articles:
            return 0.0
        
        # Simple diversity based on source distribution
        sources = {article.source for article in articles}
        source_diversity = len(sources) / max(len(articles), 1)
        
        # Simple title word diversity
        all_words = set()
        for article in articles:
            words = article.title.lower().split()
            all_words.update(words)
        
        word_diversity = min(len(all_words) / max(len(articles) * 5, 1), 1.0)
        
        return (source_diversity + word_diversity) / 2
    
    def _analyze_topic_distribution(self, articles: List[Article]) -> Dict[str, int]:
        """Analyze topic distribution (simplified)."""
        topics = {}
        
        for article in articles:
            # Simple topic extraction based on title keywords
            title_lower = article.title.lower()
            
            # Basic topic categories (can be enhanced with NLP)
            if any(word in title_lower for word in ['politique', 'élection', 'gouvernement']):
                topics['Politique'] = topics.get('Politique', 0) + 1
            elif any(word in title_lower for word in ['économie', 'économique', 'marché']):
                topics['Économie'] = topics.get('Économie', 0) + 1
            elif any(word in title_lower for word in ['sport', 'football', 'olympique']):
                topics['Sport'] = topics.get('Sport', 0) + 1
            elif any(word in title_lower for word in ['culture', 'cinéma', 'musique']):
                topics['Culture'] = topics.get('Culture', 0) + 1
            elif any(word in title_lower for word in ['santé', 'médical', 'hôpital']):
                topics['Santé'] = topics.get('Santé', 0) + 1
            else:
                topics['Actualités'] = topics.get('Actualités', 0) + 1
        
        return topics
    
    def save_hourly_batch(
        self, 
        curation_result: CurationResult, 
        timestamp: str, 
        output_dir
    ) -> str:
        """
        Save hourly batch - placeholder for v5.
        In v5, this is handled by the autonomous scraper directly.
        """
        # This method is mainly for compatibility
        # Actual saving is done in autonomous_scraper.py
        return f"v5_batch_{timestamp}.json" 