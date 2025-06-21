#!/usr/bin/env python3
"""
Better French Max - Automated Quality Curator
Inherits exact scoring logic from proven manual system
Enhanced with automation features for real-time curation
"""

import os
import sys
import json
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from automation import AUTOMATION_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ScoredArticle:
    """Article with quality scores (matches manual system structure)"""
    # Original article data
    original_data: Dict[str, Any]
    
    # Scoring (EXACT same as manual system)
    quality_score: float
    relevance_score: float
    importance_score: float
    total_score: float
    
    # Curation metadata
    curation_id: str
    curated_at: str
    rejection_reason: str = ""
    
    # Automation enhancements
    fast_tracked: bool = False
    urgency_score: float = 0.0

class AutomatedCurator:
    """
    Automated quality curator with EXACT same scoring logic as manual system
    Enhanced with real-time automation features
    """
    
    def __init__(self):
        self.curated_articles = []
        self.rejected_articles = []
        
        # EXACT same keywords as proven manual system
        self.high_relevance_keywords = {
            # Immigration & Legal
            'immigration', 'visa', 'carte de séjour', 'naturalisation', 'préfecture', 
            'titre de séjour', 'étranger', 'expatrié', 'résidence', 'citoyenneté',
            
            # Daily Life & Services
            'sécurité sociale', 'caf', 'pôle emploi', 'impôts', 'logement', 'santé',
            'transport', 'sncf', 'ratp', 'école', 'université', 'formation',
            'banque', 'assurance', 'mutuelle', 'médecin', 'hôpital',
            
            # French Culture & Society
            'culture française', 'tradition', 'laïcité', 'république', 'marianne',
            'gastronomie', 'cuisine', 'vin', 'fromage', 'baguette', 'café',
            'festival', 'patrimoine', 'monument', 'musée', 'art français',
            
            # Government & Politics (affecting daily life)
            'gouvernement', 'président', 'assemblée nationale', 'sénat', 'maire',
            'conseil municipal', 'région', 'département', 'commune', 'élection',
            'réforme', 'loi', 'décret', 'politique sociale',
            
            # Economy & Work
            'emploi', 'chômage', 'smic', 'salaire', 'retraite', 'cotisation',
            'entreprise', 'startup', 'innovation', 'économie française', 'crise',
            'inflation', 'pouvoir d\'achat', 'marché du travail',
            
            # Education & Language
            'français langue étrangère', 'fle', 'apprentissage', 'intégration',
            'cours de français', 'alliance française',
            
            # Regional Life
            'paris', 'région parisienne', 'province', 'métropole', 'banlieue',
            'quartier', 'arrondissement', 'ile-de-france'
        }
        
        self.medium_relevance_keywords = {
            # National Events & News
            'france', 'français', 'national', 'pays', 'état', 'société',
            'population', 'citoyen', 'public', 'social', 'communauté',
            
            # Current Affairs
            'actualité', 'information', 'débat', 'polémique', 'manifestation',
            'grève', 'syndical', 'droit', 'justice', 'tribunal',
            
            # Technology & Innovation
            'technologie', 'numérique', 'internet', 'intelligence artificielle',
            'startup française', 'innovation française',
            
            # Environment (affects daily life)
            'environnement', 'climat', 'pollution', 'transport public',
            'vélo', 'écologie', 'recyclage', 'énergie'
        }
        
        # Keywords that reduce relevance (EXACT same as manual system)
        self.low_relevance_keywords = {
            'people', 'célébrité', 'star', 'télé-réalité', 'scandale',
            'paparazzi', 'instagram', 'tiktok', 'influenceur',
            'gossip', 'rumeur', 'vie privée'
        }
        
        # Importance indicators (EXACT same as manual system)
        self.high_importance_indicators = {
            'breaking', 'urgent', 'alerte', 'important', 'majeur',
            'historique', 'exceptionnel', 'première fois', 'record',
            'crise', 'urgence', 'décision', 'annonce', 'officiel'
        }
        
        # Quality indicators (EXACT same as manual system)
        self.quality_indicators = {
            'analysis': ['analyse', 'enquête', 'investigation', 'reportage', 'dossier'],
            'expertise': ['expert', 'spécialiste', 'professeur', 'chercheur', 'selon'],
            'sources': ['source', 'témoin', 'déclaration', 'interview', 'entretien'],
            'context': ['contexte', 'histoire', 'background', 'explication', 'pourquoi']
        }
        
        # Quality thresholds from config
        self.quality_config = AUTOMATION_CONFIG['quality']
        
        logger.info("🎯 Automated Curator initialized with proven scoring logic")
        logger.info(f"📊 Quality threshold: {self.quality_config['min_total_score']}/30")
    
    def score_quality(self, article: Dict[str, Any]) -> float:
        """Score article quality (0-10) - EXACT same logic as manual system"""
        score = 5.0  # Base score
        
        title = (article.get('title') or '').lower()
        summary = (article.get('summary') or '').lower()
        content = (article.get('content') or '').lower()
        
        # Combine all text for analysis
        full_text = f"{title} {summary} {content}"
        
        # Quality factors
        
        # 1. Content completeness (+2)
        if content and len(content) > 200:
            score += 1.0
        if summary and len(summary) > 50:
            score += 0.5
        if article.get('author'):
            score += 0.5
        
        # 2. Writing quality indicators (+2)
        for category, keywords in self.quality_indicators.items():
            if any(keyword in full_text for keyword in keywords):
                score += 0.5
        
        # 3. Structure quality (+1)
        if len(title.split()) >= 5:  # Descriptive title
            score += 0.3
        if any(punct in title for punct in [':',  '«', '»']):  # French punctuation
            score += 0.2
        if summary and summary != title.lower():  # Unique summary
            score += 0.5
        
        # 4. Language quality (+1)
        # Check for proper French structure
        french_patterns = [
            r'\b(le|la|les|un|une|des)\b',  # Articles
            r'\b(est|sont|était|sera)\b',   # Common verbs
            r'\b(avec|dans|pour|sur|par)\b'  # Prepositions
        ]
        french_score = sum(1 for pattern in french_patterns if re.search(pattern, full_text))
        score += min(1.0, french_score * 0.2)
        
        # Quality penalties
        
        # Poor quality indicators (-2)
        poor_indicators = ['cliquez', 'buzz', 'choc', 'scandaleux', 'incroyable']
        if any(indicator in full_text for indicator in poor_indicators):
            score -= 1.0
            
        # Too short content (-1)
        if len(full_text) < 100:
            score -= 1.0
            
        # All caps title (clickbait) (-0.5)
        if title.isupper():
            score -= 0.5
        
        return max(0, min(10, score))
    
    def score_relevance(self, article: Dict[str, Any]) -> float:
        """Score relevance (0-10) for expats/immigrants - EXACT same logic as manual system"""
        score = 3.0  # Base score for French news
        
        title = (article.get('title') or '').lower()
        summary = (article.get('summary') or '').lower()
        content = (article.get('content') or '').lower()
        category = (article.get('category') or '').lower()
        
        full_text = f"{title} {summary} {content} {category}"
        
        # High relevance for expat life (+4)
        high_matches = sum(1 for keyword in self.high_relevance_keywords 
                          if keyword in full_text)
        score += min(4.0, high_matches * 0.8)
        
        # Medium relevance for French society (+2)
        medium_matches = sum(1 for keyword in self.medium_relevance_keywords 
                           if keyword in full_text)
        score += min(2.0, medium_matches * 0.3)
        
        # Category-based relevance (+1)
        relevant_categories = [
            'politique', 'société', 'économie', 'france', 'national',
            'immigration', 'education', 'culture', 'santé', 'social'
        ]
        if any(cat in category for cat in relevant_categories):
            score += 1.0
        
        # Penalties for low relevance (-3)
        low_matches = sum(1 for keyword in self.low_relevance_keywords 
                         if keyword in full_text)
        score -= min(3.0, low_matches * 1.0)
        
        # International news penalty (unless affects France) (-1)
        international_indicators = ['états-unis', 'chine', 'russie', 'ukraine', 'gaza']
        france_context = ['france', 'français', 'hexagone', 'paris', 'gouvernement']
        
        if (any(indicator in full_text for indicator in international_indicators) and
            not any(context in full_text for context in france_context)):
            score -= 1.0
        
        return max(0, min(10, score))
    
    def score_importance(self, article: Dict[str, Any]) -> float:
        """Score importance (0-10) - EXACT same logic as manual system"""
        score = 4.0  # Base score
        
        title = (article.get('title') or '').lower()
        summary = (article.get('summary') or '').lower()
        content = (article.get('content') or '').lower()
        source = (article.get('source_name') or '').lower()
        
        full_text = f"{title} {summary} {content}"
        
        # Breaking news/urgent (+2)
        if any(indicator in full_text for indicator in self.high_importance_indicators):
            score += 2.0
        
        # Government/policy news (+2)
        policy_keywords = [
            'gouvernement', 'ministre', 'président', 'assemblée', 'sénat',
            'loi', 'décret', 'réforme', 'politique', 'décision officielle'
        ]
        if any(keyword in full_text for keyword in policy_keywords):
            score += 2.0
        
        # Economic impact (+1.5)
        economic_keywords = [
            'économie', 'emploi', 'chômage', 'inflation', 'prix', 'salaire',
            'impôt', 'budget', 'crise', 'marché', 'entreprise'
        ]
        if any(keyword in full_text for keyword in economic_keywords):
            score += 1.5
        
        # Social impact (+1.5)
        social_keywords = [
            'société', 'social', 'manifestation', 'grève', 'éducation',
            'santé', 'logement', 'transport', 'sécurité', 'justice'
        ]
        if any(keyword in full_text for keyword in social_keywords):
            score += 1.5
        
        # Source reputation (+1)
        reputable_sources = [
            'le monde', 'le figaro', 'france info', 'france 24', 'rfi',
            'libération', 'le parisien', 'afp'
        ]
        if any(source_name in source for source_name in reputable_sources):
            score += 1.0
        
        # Local/regional penalty (unless major city) (-1)
        local_indicators = ['commune', 'village', 'petit', 'local']
        major_cities = ['paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes']
        
        if (any(indicator in full_text for indicator in local_indicators) and
            not any(city in full_text for city in major_cities)):
            score -= 1.0
        
        return max(0, min(10, score))
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1) - same as manual system"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def find_duplicates(self, articles: List[Dict[str, Any]], 
                       similarity_threshold: float = 0.7) -> List[List[int]]:
        """Find duplicate articles - same logic as manual system"""
        duplicate_groups = []
        processed_indices = set()
        
        for i, article1 in enumerate(articles):
            if i in processed_indices:
                continue
                
            title1 = article1.get('title', '')
            current_group = [i]
            processed_indices.add(i)
            
            for j, article2 in enumerate(articles[i+1:], i+1):
                if j in processed_indices:
                    continue
                    
                title2 = article2.get('title', '')
                similarity = self.calculate_similarity(title1, title2)
                
                if similarity > similarity_threshold:
                    current_group.append(j)
                    processed_indices.add(j)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
        
        return duplicate_groups
    
    def select_best_duplicate(self, articles: List[Dict[str, Any]], 
                            scores: List[float], indices: List[int]) -> int:
        """Select the best article from duplicates - same logic as manual system"""
        best_idx = indices[0]
        best_score = scores[indices[0]]
        
        for idx in indices[1:]:
            # Primary: highest total score
            if scores[idx] > best_score:
                best_idx = idx
                best_score = scores[idx]
            # Tiebreaker: longer content
            elif (scores[idx] == best_score and
                  len(articles[idx].get('content') or '') > 
                  len(articles[best_idx].get('content') or '')):
                best_idx = idx
        
        return best_idx
    
    def score_single_article(self, article: Dict[str, Any]) -> ScoredArticle:
        """Score a single article with all three metrics"""
        # Convert from smart scraper format if needed
        if hasattr(article, '__dict__'):
            article_data = article.__dict__
        else:
            article_data = article
        
        quality = self.score_quality(article_data)
        relevance = self.score_relevance(article_data)
        importance = self.score_importance(article_data)
        total = quality + relevance + importance
        
        # Extract urgency score if available (from smart scraper)
        urgency_score = article_data.get('urgency_score', 0.0)
        
        return ScoredArticle(
            original_data=article_data,
            quality_score=quality,
            relevance_score=relevance,
            importance_score=importance,
            total_score=total,
            curation_id=str(uuid.uuid4()),
            curated_at=datetime.now(timezone.utc).isoformat(),
            urgency_score=urgency_score
        )
    
    def fast_track_curation(self, breaking_articles: List[Any]) -> List[ScoredArticle]:
        """Fast-track curation for breaking news (optimized for speed)"""
        logger.info("🚨 Fast-track curation for breaking news...")
        
        curated = []
        
        for article in breaking_articles:
            scored_article = self.score_single_article(article)
            scored_article.fast_tracked = True
            
            # Lower threshold for breaking news (urgency matters)
            min_score = self.quality_config['min_total_score'] - 3.0
            
            if (scored_article.total_score >= min_score or 
                scored_article.urgency_score >= 3.0):
                curated.append(scored_article)
                logger.debug(f"✅ Fast-tracked: {scored_article.original_data.get('title', '')[:50]}...")
            else:
                scored_article.rejection_reason = f"low_score_breaking_{scored_article.total_score:.1f}"
        
        logger.info(f"🚨 Fast-track completed: {len(curated)} breaking news articles approved")
        return curated
    
    def full_curation(self, articles: List[Any]) -> List[ScoredArticle]:
        """Full curation process with deduplication"""
        logger.info(f"🎯 Full curation of {len(articles)} articles...")
        
        # Convert articles to dict format if needed
        article_dicts = []
        for article in articles:
            if hasattr(article, '__dict__'):
                article_dicts.append(article.__dict__)
            else:
                article_dicts.append(article)
        
        # Score all articles
        scored_articles = []
        for article in article_dicts:
            scored_article = self.score_single_article(article)
            scored_articles.append(scored_article)
        
        # Find and handle duplicates
        duplicate_groups = self.find_duplicates(article_dicts)
        total_scores = [sa.total_score for sa in scored_articles]
        
        # Track articles to remove
        to_remove = set()
        
        for group in duplicate_groups:
            best_idx = self.select_best_duplicate(article_dicts, total_scores, group)
            removed_indices = [idx for idx in group if idx != best_idx]
            to_remove.update(removed_indices)
        
        # Separate curated vs rejected
        curated = []
        rejected = []
        
        min_score = self.quality_config['min_total_score']
        
        for i, scored_article in enumerate(scored_articles):
            if i in to_remove:
                scored_article.rejection_reason = "duplicate"
                rejected.append(scored_article)
            elif scored_article.total_score < min_score:
                scored_article.rejection_reason = f"low_score_{scored_article.total_score:.1f}"
                rejected.append(scored_article)
            else:
                curated.append(scored_article)
        
        # Sort by total score (descending)
        curated.sort(key=lambda x: x.total_score, reverse=True)
        
        logger.info(f"🎯 Curation completed: {len(curated)} approved, {len(rejected)} rejected")
        logger.info(f"🔄 Duplicate groups: {len(duplicate_groups)}, articles removed: {len(to_remove)}")
        
        if curated:
            avg_score = sum(a.total_score for a in curated) / len(curated)
            logger.info(f"📊 Average quality score: {avg_score:.1f}/30")
        
        # Store results
        self.curated_articles.extend(curated)
        self.rejected_articles.extend(rejected)
        
        return curated
    
    def save_curated_articles(self, filename: str = None) -> str:
        """Save curated articles with metadata"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/live/curated_articles_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Calculate statistics
        if self.curated_articles:
            scores = {
                'quality': [a.quality_score for a in self.curated_articles],
                'relevance': [a.relevance_score for a in self.curated_articles],
                'importance': [a.importance_score for a in self.curated_articles],
                'total': [a.total_score for a in self.curated_articles]
            }
            
            stats = {}
            for score_type, values in scores.items():
                stats[score_type] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
        else:
            stats = {}
        
        data = {
            "metadata": {
                "curated_at": datetime.now(timezone.utc).isoformat(),
                "total_curated": len(self.curated_articles),
                "curator_version": "Automated Curator 1.0",
                "automation_system": "Better French Max Automated System",
                "quality_threshold": self.quality_config['min_total_score'],
                "fast_tracked_articles": len([a for a in self.curated_articles if a.fast_tracked]),
                "statistics": stats,
                "scoring_system": {
                    "quality": "0-10 based on content completeness, writing quality, structure",
                    "relevance": "0-10 for expats/immigrants living in France",
                    "importance": "0-10 from perspective of someone living in France",
                    "total": "Sum of quality + relevance + importance (0-30)"
                }
            },
            "curated_articles": [asdict(article) for article in self.curated_articles]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Curated articles saved: {filename}")
        return filename
    
    def save_rejected_articles(self, filename: str = None) -> str:
        """Save rejected articles for analysis"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/live/rejected_articles_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Group rejections by reason
        rejection_reasons = {}
        for article in self.rejected_articles:
            reason = article.rejection_reason
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        data = {
            "metadata": {
                "curated_at": datetime.now(timezone.utc).isoformat(),
                "total_rejected": len(self.rejected_articles),
                "rejection_summary": rejection_reasons,
                "curator_version": "Automated Curator 1.0"
            },
            "rejected_articles": [asdict(article) for article in self.rejected_articles]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🗑️ Rejected articles saved: {filename}")
        return filename
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality metrics summary for monitoring"""
        if not self.curated_articles:
            return {"status": "no_articles"}
        
        scores = [a.total_score for a in self.curated_articles]
        quality_scores = [a.quality_score for a in self.curated_articles]
        relevance_scores = [a.relevance_score for a in self.curated_articles]
        importance_scores = [a.importance_score for a in self.curated_articles]
        
        return {
            "status": "active",
            "total_articles": len(self.curated_articles),
            "average_total_score": sum(scores) / len(scores),
            "average_quality": sum(quality_scores) / len(quality_scores),
            "average_relevance": sum(relevance_scores) / len(relevance_scores),
            "average_importance": sum(importance_scores) / len(importance_scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "fast_tracked_count": len([a for a in self.curated_articles if a.fast_tracked]),
            "threshold_used": self.quality_config['min_total_score']
        }

# Test function for development
def test_automated_curator():
    """Test the automated curator functionality"""
    print("🧪 Testing Automated Curator...")
    
    # Sample article for testing
    test_article = {
        'title': 'Réforme de l\'immigration : nouvelles mesures pour les étudiants étrangers',
        'summary': 'Le gouvernement annonce des changements dans la politique d\'immigration concernant les étudiants étrangers en France.',
        'content': 'Le ministre de l\'Intérieur a présenté aujourd\'hui les nouvelles mesures concernant l\'immigration étudiante. Ces réformes visent à simplifier les démarches pour les étudiants étrangers tout en renforçant les contrôles.',
        'source_name': 'Le Monde',
        'author': 'Jean Dupont',
        'category': 'politique'
    }
    
    curator = AutomatedCurator()
    
    # Test scoring
    scored = curator.score_single_article(test_article)
    print(f"🎯 Quality Score: {scored.quality_score:.1f}/10")
    print(f"🎯 Relevance Score: {scored.relevance_score:.1f}/10")
    print(f"🎯 Importance Score: {scored.importance_score:.1f}/10")
    print(f"🎯 Total Score: {scored.total_score:.1f}/30")
    
    # Test fast-track curation
    curated = curator.fast_track_curation([test_article])
    print(f"🚨 Fast-track result: {len(curated)} articles approved")
    
    print("✅ Automated Curator test completed")

if __name__ == "__main__":
    test_automated_curator() 