#!/usr/bin/env python3
"""
Rolling Articles Manager - Better French Project
Robust hybrid system that maintains a chronologically sorted collection
of all articles, showing newest 100 max, regardless of daily boundaries.
"""

import json
import os
import glob
from datetime import datetime, timedelta
import logging
from pathlib import Path
import hashlib
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RollingArticlesManager:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data" / "live"
        self.website_path = self.base_path / "Project-Better-French-Website"
        self.rolling_file = self.website_path / "rolling_articles.json"
        self.backup_file = self.website_path / "rolling_articles_backup.json"
        self.max_articles = 100
        
    def validate_environment(self) -> bool:
        """Validate that required directories and files exist"""
        try:
            if not self.data_path.exists():
                logger.error(f"Data directory not found: {self.data_path}")
                return False
                
            if not self.website_path.exists():
                logger.error(f"Website directory not found: {self.website_path}")
                return False
                
            logger.info("✅ Environment validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False
    
    def load_existing_rolling_collection(self) -> List[Dict[Any, Any]]:
        """Load existing rolling collection, with backup fallback"""
        existing_articles = []
        
        # Try main file first
        if self.rolling_file.exists():
            try:
                with open(self.rolling_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'articles' in data and isinstance(data['articles'], list):
                        existing_articles = data['articles']
                        logger.info(f"✅ Loaded {len(existing_articles)} existing articles from rolling collection")
                    else:
                        logger.warning("Rolling file exists but has invalid structure")
            except Exception as e:
                logger.error(f"Error reading rolling file: {e}")
                # Try backup
                if self.backup_file.exists():
                    try:
                        with open(self.backup_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            existing_articles = data.get('articles', [])
                            logger.info(f"✅ Recovered {len(existing_articles)} articles from backup")
                    except Exception as backup_error:
                        logger.error(f"Backup recovery failed: {backup_error}")
        
        return existing_articles
    
    def get_daily_files(self) -> List[Path]:
        """Get all daily curated article files, sorted by date"""
        try:
            pattern = str(self.data_path / "curated_articles_*.json")
            files = glob.glob(pattern)
            
            # Sort by filename (which contains date)
            sorted_files = sorted([Path(f) for f in files], reverse=True)
            
            logger.info(f"✅ Found {len(sorted_files)} daily files")
            return sorted_files
            
        except Exception as e:
            logger.error(f"Error getting daily files: {e}")
            return []
    
    def load_articles_from_daily_files(self, max_days: int = 30) -> List[Dict[Any, Any]]:
        """Load articles from daily files with robust error handling"""
        all_articles = []
        daily_files = self.get_daily_files()
        
        for file_path in daily_files[:max_days]:  # Limit to recent files
            try:
                logger.info(f"Processing: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different file formats
                articles = []
                if 'articles' in data:
                    articles = data['articles']
                elif 'curated_articles' in data:
                    # Convert curated format to standard format
                    for curated in data['curated_articles']:
                        if 'original_data' in curated:
                            article = curated['original_data'].copy()
                            # Add curation metadata
                            article['quality_score'] = curated.get('quality_score', 0)
                            article['relevance_score'] = curated.get('relevance_score', 0)
                            article['importance_score'] = curated.get('importance_score', 0)
                            article['total_score'] = curated.get('total_score', 0)
                            article['curated_at'] = curated.get('curated_at')
                            articles.append(article)
                
                if articles:
                    all_articles.extend(articles)
                    logger.info(f"✅ Loaded {len(articles)} articles from {file_path.name}")
                else:
                    logger.warning(f"No articles found in {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"✅ Total articles loaded from daily files: {len(all_articles)}")
        return all_articles
    
    def normalize_article(self, article: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize article structure and add missing fields"""
        normalized = article.copy()
        
        # Ensure required fields exist
        if 'title' not in normalized:
            normalized['title'] = normalized.get('original_article_title', 'Unknown Title')
        
        if 'link' not in normalized:
            normalized['link'] = normalized.get('original_article_link', '')
        
        # Add article hash for deduplication
        content_for_hash = f"{normalized.get('title', '')}{normalized.get('link', '')}"
        normalized['article_id'] = hashlib.md5(content_for_hash.encode()).hexdigest()
        
        return normalized
    
    def parse_article_date(self, article: Dict[Any, Any]) -> datetime:
        """Parse article date from multiple possible fields"""
        date_fields = ['published', 'published_date', 'curated_at', 'added_at', 'scraped_at']
        
        for field in date_fields:
            if field in article and article[field]:
                try:
                    date_str = str(article[field])
                    
                    # Try different date formats
                    formats = [
                        '%Y-%m-%dT%H:%M:%S.%f%z',      # 2025-06-10T20:24:47.123456+00:00
                        '%Y-%m-%dT%H:%M:%S%z',         # 2025-06-10T20:24:47+00:00
                        '%Y-%m-%dT%H:%M:%S.%f',        # 2025-06-10T20:24:47.123456
                        '%Y-%m-%dT%H:%M:%S',           # 2025-06-10T20:24:47
                        '%a, %d %b %Y %H:%M:%S %Z',    # Tue, 10 Jun 2025 20:24:47 GMT
                        '%a, %d %b %Y %H:%M:%S %z',    # Tue, 10 Jun 2025 20:24:47 +0000
                        '%Y-%m-%d %H:%M:%S',           # 2025-06-10 20:24:47
                        '%Y-%m-%d'                     # 2025-06-10
                    ]
                    
                    for fmt in formats:
                        try:
                            # Handle timezone variations
                            clean_date = date_str.replace('+00:00', '+0000').replace('GMT', '+0000')
                            return datetime.strptime(clean_date, fmt)
                        except ValueError:
                            continue
                            
                except Exception:
                    continue
        
        # Fallback to current time
        logger.warning(f"Could not parse date for article: {article.get('title', 'Unknown')[:50]}")
        return datetime.now()
    
    def remove_duplicates(self, articles: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """Remove duplicate articles based on multiple criteria"""
        seen_ids = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            normalized = self.normalize_article(article)
            article_id = normalized['article_id']
            title_clean = normalized.get('title', '').strip().lower()
            
            # Skip if duplicate by ID or very similar title
            if article_id in seen_ids:
                continue
                
            if title_clean and len(title_clean) > 20:  # Only check substantial titles
                if title_clean in seen_titles:
                    continue
                seen_titles.add(title_clean)
            
            seen_ids.add(article_id)
            unique_articles.append(normalized)
        
        removed_count = len(articles) - len(unique_articles)
        logger.info(f"✅ Removed {removed_count} duplicates, kept {len(unique_articles)} unique articles")
        return unique_articles
    
    def sort_articles_chronologically(self, articles: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """Sort articles by publication date, newest first"""
        try:
            def get_sort_key(article):
                return self.parse_article_date(article)
            
            sorted_articles = sorted(articles, key=get_sort_key, reverse=True)
            logger.info(f"✅ Sorted {len(sorted_articles)} articles chronologically")
            return sorted_articles
            
        except Exception as e:
            logger.error(f"Error sorting articles: {e}")
            return articles
    
    def create_rolling_collection(self) -> bool:
        """Main method to create/update the rolling collection"""
        try:
            logger.info("🚀 Starting robust rolling collection creation...")
            
            # Step 1: Validate environment
            if not self.validate_environment():
                return False
            
            # Step 2: Load existing articles
            existing_articles = self.load_existing_rolling_collection()
            
            # Step 3: Load new articles from daily files
            daily_articles = self.load_articles_from_daily_files()
            
            # Step 4: Combine all articles
            all_articles = existing_articles + daily_articles
            
            if not all_articles:
                logger.warning("No articles found to process")
                return False
            
            # Step 5: Remove duplicates
            unique_articles = self.remove_duplicates(all_articles)
            
            # Step 6: Sort chronologically
            sorted_articles = self.sort_articles_chronologically(unique_articles)
            
            # Step 7: Keep only newest articles (max limit)
            final_articles = sorted_articles[:self.max_articles]
            
            actual_count = len(final_articles)
            logger.info(f"✅ Final collection: {actual_count} articles (max: {self.max_articles})")
            
            # Step 8: Create metadata
            metadata = {
                "updated_at": datetime.now().isoformat(),
                "total_articles": actual_count,
                "collection_type": "rolling_chronological",
                "max_articles": self.max_articles,
                "automation_system": "Better French Rolling Articles Manager v2.0",
                "website_version": "2.0"
            }
            
            # Step 9: Create final data structure
            rolling_data = {
                "metadata": metadata,
                "articles": final_articles
            }
            
            # Step 10: Save with backup
            return self.save_rolling_collection(rolling_data)
            
        except Exception as e:
            logger.error(f"❌ Critical error in rolling collection creation: {e}")
            return False
    
    def save_rolling_collection(self, data: Dict[Any, Any]) -> bool:
        """Save rolling collection with backup and validation"""
        try:
            # Create backup of existing file
            if self.rolling_file.exists():
                logger.info("Creating backup of existing rolling collection...")
                import shutil
                shutil.copy2(self.rolling_file, self.backup_file)
            
            # Save new data
            with open(self.rolling_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Validate saved file
            with open(self.rolling_file, 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
                if 'articles' not in validation_data:
                    raise ValueError("Saved file missing articles")
            
            logger.info(f"✅ Rolling collection saved successfully: {self.rolling_file}")
            logger.info(f"📊 Final stats: {len(data['articles'])} articles, updated at {data['metadata']['updated_at']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving rolling collection: {e}")
            return False

def main():
    """Main execution function with comprehensive error handling"""
    logger.info("🚀 Starting Rolling Articles Manager v2.0...")
    
    try:
        logger.info("⚠️ RollingArticlesManager disabled (AI-only strategy in effect). Skipping collection build.")
        return 0
            
    except Exception as e:
        logger.error(f"❌ Critical system error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 