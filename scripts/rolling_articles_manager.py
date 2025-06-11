#!/usr/bin/env python3
"""
Rolling Articles Manager - Better French Project
Maintains a rolling collection of the newest 100 curated articles
"""

import json
import os
import glob
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RollingArticlesManager:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data" / "live"
        self.website_path = self.base_path / "Project-Better-French-Website"
        self.rolling_file = self.website_path / "rolling_100_articles.json"
        
    def collect_recent_articles(self, days_back=14):
        """Collect articles from the last N days of curated files"""
        all_articles = []
        
        # Get all curated article files from recent days
        pattern = str(self.data_path / "curated_articles_*.json")
        curated_files = sorted(glob.glob(pattern), reverse=True)  # Newest first
        
        logger.info(f"Found {len(curated_files)} curated article files")
        
        for file_path in curated_files[:days_back]:  # Limit to recent files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Handle both current_articles.json (articles) and curated_articles.json (curated_articles)
                if 'articles' in data:
                    articles = data['articles']
                    logger.info(f"Loaded {len(articles)} articles from {os.path.basename(file_path)}")
                    all_articles.extend(articles)
                elif 'curated_articles' in data:
                    curated_articles = data['curated_articles']
                    logger.info(f"Loaded {len(curated_articles)} curated articles from {os.path.basename(file_path)}")
                    # Convert curated format to standard format
                    for curated in curated_articles:
                        if 'original_data' in curated:
                            # Merge curated metadata with original data
                            article = curated['original_data'].copy()
                            article['quality_score'] = curated.get('quality_score', 0)
                            article['relevance_score'] = curated.get('relevance_score', 0) 
                            article['importance_score'] = curated.get('importance_score', 0)
                            article['total_score'] = curated.get('total_score', 0)
                            article['curated_at'] = curated.get('curated_at')
                            all_articles.append(article)
                    
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
                
        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles
    
    def remove_duplicates(self, articles):
        """Remove duplicate articles based on title and link"""
        seen = set()
        unique_articles = []
        
        for article in articles:
            # Create unique identifier using title and link (handle different field names)
            title = article.get('title', '') or article.get('original_article_title', '')
            link = article.get('link', '') or article.get('original_article_link', '')
            identifier = (
                title.strip().lower(),
                link.strip()
            )
            
            if identifier not in seen and identifier[0] and identifier[1]:
                seen.add(identifier)
                unique_articles.append(article)
                
        logger.info(f"Removed {len(articles) - len(unique_articles)} duplicates")
        return unique_articles
    
    def sort_by_recency(self, articles):
        """Sort articles by published date, newest first"""
        def get_sort_key(article):
            # Try multiple date fields
            date_fields = ['published', 'published_date', 'added_at', 'curated_at']
            
            for field in date_fields:
                if field in article and article[field]:
                    try:
                        # Handle different date formats
                        date_str = article[field]
                        if isinstance(date_str, str):
                            # Try parsing different formats
                            for fmt in ['%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z', 
                                      '%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%d %H:%M:%S']:
                                try:
                                    return datetime.strptime(date_str.replace('+00:00', '+0000'), fmt)
                                except:
                                    continue
                    except:
                        continue
            
            # Fallback to current time if no valid date found
            return datetime.now()
        
        sorted_articles = sorted(articles, key=get_sort_key, reverse=True)
        logger.info(f"Sorted {len(sorted_articles)} articles by recency")
        return sorted_articles
    
    def create_rolling_collection(self, max_articles=100):
        """Create the rolling collection of newest articles"""
        logger.info("Creating rolling 100 articles collection...")
        
        # Step 1: Collect recent articles
        all_articles = self.collect_recent_articles()
        
        if not all_articles:
            logger.warning("No articles found to create rolling collection")
            return False
            
        # Step 2: Remove duplicates
        unique_articles = self.remove_duplicates(all_articles)
        
        # Step 3: Sort by recency
        sorted_articles = self.sort_by_recency(unique_articles)
        
        # Step 4: Take newest 100
        rolling_articles = sorted_articles[:max_articles]
        
        logger.info(f"Selected top {len(rolling_articles)} articles for rolling collection")
        
        # Step 5: Create metadata
        metadata = {
            "updated_at": datetime.now().isoformat(),
            "total_articles": len(rolling_articles),
            "collection_type": "rolling_100",
            "max_articles": max_articles,
            "automation_system": "Better French Rolling Articles Manager",
            "website_version": "2.0"
        }
        
        # Step 6: Save rolling collection
        rolling_data = {
            "metadata": metadata,
            "articles": rolling_articles
        }
        
        try:
            with open(self.rolling_file, 'w', encoding='utf-8') as f:
                json.dump(rolling_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Rolling collection saved: {self.rolling_file}")
            logger.info(f"📊 Collection stats: {len(rolling_articles)} articles, updated at {metadata['updated_at']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving rolling collection: {e}")
            return False
    
    def update_website_pointer(self):
        """Update website to use rolling collection (optional fallback maintenance)"""
        try:
            # Keep current_articles.json as fallback, but create rolling as primary
            if self.rolling_file.exists():
                # Create a symlink or copy for compatibility if needed
                logger.info("✅ Rolling collection ready for website use")
                return True
        except Exception as e:
            logger.error(f"Error updating website pointer: {e}")
            return False

def main():
    """Main execution function"""
    logger.info("🚀 Starting Rolling Articles Manager...")
    
    manager = RollingArticlesManager()
    
    # Create rolling collection
    success = manager.create_rolling_collection(max_articles=100)
    
    if success:
        manager.update_website_pointer()
        logger.info("✅ Rolling articles management completed successfully!")
    else:
        logger.error("❌ Rolling articles management failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 