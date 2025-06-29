#!/usr/bin/env python3
"""
AI Engine v5: Intelligent Curator
Handles semantic deduplication and topic-aware article selection.

SOLVES THE "HEAT WAVE SPAM" PROBLEM:
- Recognizes "heat wave" = "heat waves" = "canicule" (semantic similarity)
- Analyzes existing website topics to avoid oversaturation
- Selects best article per topic when overlap occurs
- Ensures diverse, balanced content selection
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Article with enhanced metadata for intelligent curation."""
    title: str
    summary: str
    link: str
    source: str
    published_date: str
    content: str = ""
    
    # AI Engine v5 curation metadata
    topics: List[str] = None
    quality_score: float = 0.0
    novelty_score: float = 0.0
    semantic_fingerprint: str = ""
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []

@dataclass
class CurationResult:
    """Result of intelligent curation process."""
    selected_articles: List[Article]
    rejected_count: int
    rejection_reasons: Dict[str, int]
    topic_distribution: Dict[str, int]
    diversity_score: float
    avg_quality: float

class IntelligentCurator:
    """
    AI Engine v5 Intelligent Curator
    
    THE CORE INNOVATION: Prevents topic spam through semantic understanding
    
    Example Problem Solved:
    ❌ Before: ["Heat wave in Paris", "Canicule à Lyon", "Hot weather continues", "Heat waves grip France"]  
    ✅ After: Recognizes these as SAME topic, selects best 1-2 articles
    
    How:
    1. Semantic similarity detection (multilingual)
    2. Topic extraction and analysis  
    3. Website-aware curation (considers existing 100 articles)
    4. Quality-based selection within topics
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
        # Simple but effective similarity detection
        self.stop_words = {
            'french': {'le', 'la', 'les', 'de', 'du', 'des', 'à', 'au', 'aux', 'et', 'ou', 'pour', 'avec', 'dans', 'sur', 'par'},
            'english': {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        }
        
        # Topic keyword mappings (expandable)
        self.topic_keywords = {
            'weather': {
                'heat': ['canicule', 'heat wave', 'hot weather', 'température', 'chaleur', 'fortes chaleurs'],
                'storms': ['orage', 'storm', 'thunder', 'lightning', 'tempête'],
                'rain': ['pluie', 'rain', 'flooding', 'inondation'],
                'cold': ['froid', 'cold', 'neige', 'snow', 'gel', 'freeze']
            },
            'politics': {
                'government': ['gouvernement', 'government', 'ministre', 'minister', 'président', 'president'],
                'elections': ['élection', 'election', 'vote', 'ballot', 'candidat', 'candidate'],
                'policy': ['politique', 'policy', 'loi', 'law', 'réforme', 'reform']
            },
            'sports': {
                'football': ['football', 'soccer', 'foot', 'fifa', 'coupe du monde'],
                'olympics': ['olympique', 'olympics', 'jeux olympiques', 'médaille', 'medal'],
                'tennis': ['tennis', 'roland garros', 'wimbledon', 'open']
            },
            'economy': {
                'business': ['entreprise', 'business', 'company', 'économie', 'economy'],
                'finance': ['banque', 'bank', 'financial', 'bourse', 'stock market'],
                'employment': ['emploi', 'employment', 'jobs', 'chômage', 'unemployment']
            }
        }
        
        logger.info("🧠 Intelligent Curator v5 initialized - SEMANTIC DEDUPLICATION ACTIVE")
    
    def _default_config(self) -> Dict:
        """Default configuration for intelligent curation."""
        return {
            'semantic_similarity_threshold': 0.7,  # How similar before considered duplicate
            'max_articles_per_topic': 2,           # Max articles per topic category
            'target_article_count': 10,            # Target number to select
            'quality_threshold': 0.4,              # Minimum quality score
            'novelty_weight': 0.4,                 # Weight for topic novelty vs existing website
            'quality_weight': 0.6                  # Weight for article quality
        }
    
    def curate_articles(self, 
                       candidates: List[Article], 
                       existing_website_articles: List[Article]) -> CurationResult:
        """
        MAIN METHOD: Select 10 diverse, high-quality articles
        
        Process:
        1. Analyze existing website topics
        2. Extract topics from candidates  
        3. Semantic deduplication
        4. Topic-aware selection
        5. Quality ranking
        """
        logger.info(f"🎯 CURATING: {len(candidates)} candidates vs {len(existing_website_articles)} existing")
        
        # Step 1: Understand what's already on the website
        existing_topics = self._analyze_existing_topics(existing_website_articles)
        logger.info(f"📊 Website has: {dict(list(existing_topics.items())[:5])}...")
        
        # Step 2: Process all candidate articles
        processed_candidates = []
        for article in candidates:
            processed = self._analyze_article(article, existing_topics)
            processed_candidates.append(processed)
        
        # Step 3: Remove semantic duplicates
        deduplicated = self._remove_semantic_duplicates(processed_candidates)
        logger.info(f"🔄 After deduplication: {len(deduplicated)}/{len(candidates)} articles")
        
        # Step 4: Select best articles ensuring topic diversity
        selected = self._select_diverse_articles(deduplicated, existing_topics)
        
        # Step 5: Create result summary
        result = self._create_result_summary(selected, candidates, existing_topics)
        
        logger.info(f"✅ SELECTED: {len(selected)} articles with {result.diversity_score:.1f} diversity score")
        return result
    
    def _analyze_existing_topics(self, articles: List[Article]) -> Dict[str, int]:
        """Count what topics are already covered on website."""
        topic_counts = {}
        
        for article in articles:
            topics = self._extract_topics(f"{article.title} {article.summary}")
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return topic_counts
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from article text using keyword matching."""
        text_lower = text.lower()
        found_topics = []
        
        # Check each topic category
        for main_topic, subcategories in self.topic_keywords.items():
            topic_found = False
            for subcategory, keywords in subcategories.items():
                if any(keyword in text_lower for keyword in keywords):
                    found_topics.append(f"{main_topic}_{subcategory}")
                    topic_found = True
                    break
            
            # If specific subcategory not found but main topic keywords present
            if not topic_found:
                main_keywords = [kw for subcat in subcategories.values() for kw in subcat]
                if any(keyword in text_lower for keyword in main_keywords[:3]):  # Check first few
                    found_topics.append(main_topic)
        
        # Extract location-based topics
        location_indicators = ['paris', 'lyon', 'marseille', 'france', 'french', 'français']
        if any(loc in text_lower for loc in location_indicators):
            found_topics.append('france_local')
        
        # Extract urgency indicators
        urgent_indicators = ['urgent', 'breaking', 'emergency', 'alerte', 'immediate']
        if any(urgent in text_lower for urgent in urgent_indicators):
            found_topics.append('urgent_news')
        
        return list(set(found_topics))  # Remove duplicates
    
    def _analyze_article(self, article: Article, existing_topics: Dict[str, int]) -> Article:
        """Analyze single article: extract topics, calculate scores."""
        
        # Extract topics
        text = f"{article.title} {article.summary}"
        article.topics = self._extract_topics(text)
        
        # Calculate quality score (0-1)
        quality_factors = {
            'title_length': self._score_length(article.title, optimal=60, min_val=20, max_val=100),
            'summary_length': self._score_length(article.summary, optimal=150, min_val=50, max_val=300),
            'has_content': 1.0 if article.content.strip() else 0.3,
            'topic_coverage': min(len(article.topics), 3) / 3,  # 1-3 topics is good
            'source_quality': self._score_source_quality(article.source)
        }
        article.quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        # Calculate novelty score (how new is this topic mix?)
        if article.topics:
            novelty_scores = []
            for topic in article.topics:
                existing_count = existing_topics.get(topic, 0)
                # More novel if topic is less represented on website
                novelty = 1.0 / (1.0 + existing_count * 0.2)
                novelty_scores.append(novelty)
            article.novelty_score = sum(novelty_scores) / len(novelty_scores)
        else:
            article.novelty_score = 0.5  # Neutral if no topics identified
        
        # Create semantic fingerprint for similarity detection
        article.semantic_fingerprint = self._create_semantic_fingerprint(text)
        
        return article
    
    def _score_length(self, text: str, optimal: int, min_val: int, max_val: int) -> float:
        """Score text length (1.0 = optimal, lower for too short/long)."""
        length = len(text)
        if length < min_val:
            return length / min_val * 0.5  # Penalty for too short
        elif length > max_val:
            return max(0.3, 1.0 - (length - max_val) / max_val)  # Penalty for too long
        else:
            # Closer to optimal = higher score
            distance_from_optimal = abs(length - optimal)
            max_distance = max(optimal - min_val, max_val - optimal)
            return 1.0 - (distance_from_optimal / max_distance) * 0.3
    
    def _score_source_quality(self, source: str) -> float:
        """Simple source quality scoring."""
        trusted_sources = ['le figaro', 'le monde', 'liberation', 'bfm', 'france24', 'reuters']
        source_lower = source.lower()
        
        if any(trusted in source_lower for trusted in trusted_sources):
            return 1.0
        else:
            return 0.7  # Neutral for unknown sources
    
    def _create_semantic_fingerprint(self, text: str) -> str:
        """Create fingerprint for semantic similarity detection."""
        # Normalize text: lowercase, remove stop words, extract key terms
        words = text.lower().split()
        
        # Remove stop words
        all_stop_words = self.stop_words['french'] | self.stop_words['english']
        meaningful_words = [w for w in words if w not in all_stop_words and len(w) > 2]
        
        # Sort and join to create fingerprint
        fingerprint = ' '.join(sorted(meaningful_words[:10]))  # Top 10 meaningful words
        return fingerprint
    
    def _remove_semantic_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove articles that are semantically similar."""
        if len(articles) <= 1:
            return articles
        
        # Group articles by similarity
        similarity_groups = []
        used_indices = set()
        
        for i in range(len(articles)):
            if i in used_indices:
                continue
            
            current_group = [i]
            
            # Find similar articles
            for j in range(i + 1, len(articles)):
                if j in used_indices:
                    continue
                
                similarity = self._calculate_similarity(articles[i], articles[j])
                if similarity > self.config['semantic_similarity_threshold']:
                    current_group.append(j)
                    used_indices.add(j)
            
            similarity_groups.append(current_group)
            used_indices.add(i)
        
        # Select best article from each group
        selected_articles = []
        for group in similarity_groups:
            group_articles = [articles[idx] for idx in group]
            
            if len(group) > 1:
                # Multiple similar articles - select best quality
                best_article = max(group_articles, key=lambda a: a.quality_score)
                logger.info(f"📝 Duplicate group found: kept '{best_article.title[:40]}...', removed {len(group)-1} similar")
            else:
                # Single article, keep it
                best_article = group_articles[0]
            
            selected_articles.append(best_article)
        
        return selected_articles
    
    def _calculate_similarity(self, article1: Article, article2: Article) -> float:
        """Calculate semantic similarity between two articles."""
        
        # Compare semantic fingerprints (word overlap)
        words1 = set(article1.semantic_fingerprint.split())
        words2 = set(article2.semantic_fingerprint.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        word_similarity = intersection / union if union > 0 else 0.0
        
        # Topic overlap
        topics1 = set(article1.topics)
        topics2 = set(article2.topics)
        
        if topics1 and topics2:
            topic_intersection = len(topics1 & topics2)
            topic_union = len(topics1 | topics2)
            topic_similarity = topic_intersection / topic_union
        else:
            topic_similarity = 0.0
        
        # Combined similarity (weighted average)
        overall_similarity = 0.7 * word_similarity + 0.3 * topic_similarity
        
        return overall_similarity
    
    def _select_diverse_articles(self, articles: List[Article], existing_topics: Dict[str, int]) -> List[Article]:
        """Select articles ensuring topic diversity and high quality."""
        
        target_count = self.config['target_article_count']
        max_per_topic = self.config['max_articles_per_topic']
        
        # Calculate combined scores
        for article in articles:
            combined_score = (
                self.config['quality_weight'] * article.quality_score +
                self.config['novelty_weight'] * article.novelty_score
            )
            article.combined_score = combined_score
        
        # Sort by combined score
        sorted_articles = sorted(articles, key=lambda a: a.combined_score, reverse=True)
        
        # Select ensuring topic diversity
        selected = []
        topic_usage = {}
        
        for article in sorted_articles:
            if len(selected) >= target_count:
                break
            
            # Check topic constraints
            can_select = True
            for topic in article.topics:
                if topic_usage.get(topic, 0) >= max_per_topic:
                    can_select = False
                    break
            
            # Select if constraints met and quality threshold passed
            if can_select and article.quality_score >= self.config['quality_threshold']:
                selected.append(article)
                
                # Update topic usage
                for topic in article.topics:
                    topic_usage[topic] = topic_usage.get(topic, 0) + 1
                
                logger.info(f"✅ Selected: '{article.title[:50]}...' (Q:{article.quality_score:.2f}, N:{article.novelty_score:.2f})")
        
        return selected
    
    def _create_result_summary(self, selected: List[Article], all_candidates: List[Article], existing_topics: Dict[str, int]) -> CurationResult:
        """Create comprehensive result summary."""
        
        # Topic distribution of selected articles
        topic_dist = {}
        for article in selected:
            for topic in article.topics:
                topic_dist[topic] = topic_dist.get(topic, 0) + 1
        
        # Calculate diversity score
        unique_topics = len(topic_dist)
        total_articles = len(selected) if selected else 1
        diversity_score = unique_topics / total_articles
        
        # Average quality
        avg_quality = sum(a.quality_score for a in selected) / len(selected) if selected else 0
        
        # Rejection analysis
        selected_links = {a.link for a in selected}
        rejected_count = len([a for a in all_candidates if a.link not in selected_links])
        
        # Simplified rejection reasons (for summary)
        rejection_reasons = {
            'quality_too_low': 0,
            'topic_oversaturation': 0,
            'semantic_duplicate': 0
        }
        
        # Estimate rejection reasons (simplified)
        for article in all_candidates:
            if article.link not in selected_links:
                if hasattr(article, 'quality_score') and article.quality_score < self.config['quality_threshold']:
                    rejection_reasons['quality_too_low'] += 1
                else:
                    rejection_reasons['topic_oversaturation'] += 1
        
        return CurationResult(
            selected_articles=selected,
            rejected_count=rejected_count,
            rejection_reasons=rejection_reasons,
            topic_distribution=topic_dist,
            diversity_score=diversity_score,
            avg_quality=avg_quality
        )
    
    def save_hourly_batch(self, result: CurationResult, timestamp: str, output_dir: Path):
        """Save curated batch for AI processing workflow."""
        
        # Create filename with timestamp
        filename = f"hourly_batch_{timestamp}.json"
        output_path = output_dir / filename
        
        # Prepare data
        batch_data = {
            'metadata': {
                'timestamp': timestamp,
                'curator_version': 'v5_intelligent',
                'article_count': len(result.selected_articles),
                'diversity_score': result.diversity_score,
                'avg_quality': result.avg_quality,
                'topic_distribution': result.topic_distribution,
                'curation_stats': {
                    'rejected_count': result.rejected_count,
                    'rejection_reasons': result.rejection_reasons
                }
            },
            'articles': [
                {
                    'title': a.title,
                    'summary': a.summary,
                    'link': a.link,
                    'source': a.source,
                    'published_date': a.published_date,
                    'content': a.content,
                    'topics': a.topics,
                    'quality_score': a.quality_score,
                    'novelty_score': a.novelty_score
                }
                for a in result.selected_articles
            ]
        }
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Saved hourly batch: {output_path}")
        logger.info(f"📊 {len(result.selected_articles)} articles, diversity: {result.diversity_score:.2f}")
        
        return output_path

# Example usage
if __name__ == "__main__":
    curator = IntelligentCurator()
    
    # Test with sample data
    candidates = [
        Article("Canicule exceptionnelle à Paris", "Températures record dans la capitale", "http://ex.com/1", "Le Figaro", "2025-06-29"),
        Article("Heat wave grips France", "Extreme temperatures across the country", "http://ex.com/2", "France24", "2025-06-29"),
        Article("Élections législatives: résultats", "Nouveau gouvernement en formation", "http://ex.com/3", "Le Monde", "2025-06-29"),
    ]
    
    existing = [
        Article("Previous weather story", "Old content", "http://ex.com/old", "Source", "2025-06-20")
    ]
    
    result = curator.curate_articles(candidates, existing)
    print(f"🎯 Curated: {len(result.selected_articles)} articles")
    print(f"📊 Topics: {result.topic_distribution}")
    print(f"🌟 Quality: {result.avg_quality:.2f}, Diversity: {result.diversity_score:.2f}") 