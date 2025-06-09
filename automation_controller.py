#!/usr/bin/env python3
"""
Better French Max - Automation Controller
Main orchestration script that integrates:
1. Smart Scraper (collects fresh French news)
2. Quality Curator (filters & scores articles)  
3. AI Processor (adds contextual learning)
4. Website Updater (publishes to live site)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import importlib.util

# Add config and scripts to path
sys.path.extend([
    os.path.join(os.path.dirname(__file__), 'config'),
    os.path.join(os.path.dirname(__file__), 'scripts')
])

# Import configurations - API config sets up environment variables
import api_config  # This sets up OpenRouter API key in environment
from automation import AUTOMATION_CONFIG
from smart_scraper import SmartScraper
from quality_curator import AutomatedCurator
spec = importlib.util.spec_from_file_location("AI_Engine", os.path.join(os.path.dirname(__file__), "scripts", "AI-Engine.py"))
AI_Engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AI_Engine)
CostOptimizedAIProcessor = AI_Engine.CostOptimizedAIProcessor
from website_updater import LiveWebsiteUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation_controller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutomationController:
    """
    Master controller for the automated French learning system
    Orchestrates the complete pipeline from news scraping to website publication
    """
    
    def __init__(self):
        self.config = AUTOMATION_CONFIG
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data', 'live')
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize components
        self.scraper = SmartScraper()
        self.curator = AutomatedCurator()
        self.ai_processor = CostOptimizedAIProcessor()
        self.website_updater = LiveWebsiteUpdater()
        
        # Pipeline statistics
        self.pipeline_stats = {
            'session_started': datetime.now(timezone.utc).isoformat(),
            'articles_scraped': 0,
            'articles_curated': 0,
            'articles_ai_processed': 0,
            'articles_published': 0,
            'processing_times': {},
            'errors': []
        }
        
        logger.info("🚀 Automation Controller initialized")
        logger.info(f"💰 Daily AI budget: ${self.config['cost']['daily_cost_limit']}")
        logger.info(f"📄 Max AI articles: {self.config['cost']['max_ai_articles_per_day']}")
    
    def run_breaking_news_scan(self) -> Dict[str, Any]:
        """Run urgent breaking news scan (every 30 minutes)"""
        logger.info("🚨 Starting breaking news scan...")
        return self._run_pipeline(
            scan_type="breaking_news",
            max_articles_per_source=10,
            total_article_limit=50,
            time_window_hours=2,
            prioritize_ai=True
        )
    
    def run_regular_update_scan(self) -> Dict[str, Any]:
        """Run regular content update scan (every 2 hours)"""
        logger.info("📰 Starting regular news update scan...")
        return self._run_pipeline(
            scan_type="regular_update", 
            max_articles_per_source=20,
            total_article_limit=200,
            time_window_hours=6,
            prioritize_ai=True
        )
    
    def _run_pipeline(self, scan_type: str, max_articles_per_source: int, 
                     total_article_limit: int, time_window_hours: int, 
                     prioritize_ai: bool = True) -> Dict[str, Any]:
        """Execute the complete automation pipeline"""
        
        start_time = time.time()
        pipeline_id = f"{scan_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🔄 Pipeline {pipeline_id} starting...")
        
        try:
            # STEP 1: Smart Scraping
            logger.info("📡 STEP 1: Smart News Scraping...")
            step1_start = time.time()
            
            if scan_type == "breaking_news":
                # Use breaking news scan for urgent updates
                scraped_articles = self.scraper.quick_breaking_news_scan(
                    self.config['scheduling']['breaking_news_keywords']
                )
            else:
                # Use comprehensive scrape for regular updates
                scraped_articles = self.scraper.comprehensive_scrape()
            
            step1_time = time.time() - step1_start
            self.pipeline_stats['articles_scraped'] = len(scraped_articles)
            self.pipeline_stats['processing_times']['scraping'] = step1_time
            
            if not scraped_articles:
                logger.warning("⚠️ No articles found during scraping")
                return self._create_pipeline_result(pipeline_id, "no_articles", start_time)
            
            logger.info(f"✅ Scraped {len(scraped_articles)} articles in {step1_time:.2f}s")
            
            # STEP 2: Quality Curation
            logger.info("🎯 STEP 2: Quality Curation & Scoring...")
            step2_start = time.time()
            
            if scan_type == "breaking_news" and prioritize_ai:
                # Use fast-track curation for breaking news
                curated_articles = self.curator.fast_track_curation(scraped_articles)
            else:
                # Use full curation for regular updates
                curated_articles = self.curator.full_curation(scraped_articles)
            
            step2_time = time.time() - step2_start
            self.pipeline_stats['articles_curated'] = len(curated_articles)
            self.pipeline_stats['processing_times']['curation'] = step2_time
            
            if not curated_articles:
                logger.warning("⚠️ No articles passed quality curation")
                return self._create_pipeline_result(pipeline_id, "no_quality_articles", start_time)
            
            logger.info(f"✅ Curated {len(curated_articles)} quality articles in {step2_time:.2f}s")
            
            # STEP 3: AI Processing (Quality-First Approach)
            logger.info("🤖 STEP 3: AI Enhancement with Contextual Learning...")
            step3_start = time.time()
            
            website_articles = []
            ai_processed_articles = []
            
            if self.config['cost']['enable_realtime_ai_processing']:
                # Convert ScoredArticle objects to format expected by AI processor
                ai_candidates = []
                for scored_article in curated_articles:
                    # Extract data in the format AI processor expects
                    article_for_ai = {
                        'original_data': scored_article.original_data,
                        'quality_score': scored_article.quality_score,
                        'relevance_score': scored_article.relevance_score,
                        'importance_score': scored_article.importance_score,
                        'total_score': scored_article.total_score,
                        'curation_id': scored_article.curation_id,
                        'curated_at': scored_article.curated_at,
                        'fast_tracked': scored_article.fast_tracked
                    }
                    
                    # Only process articles that meet the AI quality threshold
                    if scored_article.total_score >= self.config['cost']['quality_threshold_for_ai']:
                        ai_candidates.append(article_for_ai)
                
                logger.info(f"🎯 {len(ai_candidates)}/{len(curated_articles)} articles qualify for AI processing")
                
                # Try AI processing
                try:
                    ai_processed_articles = self.ai_processor.batch_process_articles(ai_candidates)
                    step3_time = time.time() - step3_start
                    self.pipeline_stats['articles_ai_processed'] = len(ai_processed_articles)
                    self.pipeline_stats['processing_times']['ai_processing'] = step3_time
                    
                    if ai_processed_articles:
                        logger.info(f"✅ AI processed {len(ai_processed_articles)} articles in {step3_time:.2f}s")
                        # Convert AI processed articles to website format
                        website_articles = self._convert_to_website_format(ai_processed_articles, "ai_enhanced")
                    else:
                        logger.warning("⚠️ AI processing returned 0 articles - falling back to curated format")
                        website_articles = self._convert_curated_to_website_format(curated_articles)
                        
                except Exception as ai_error:
                    logger.error(f"❌ AI processing failed: {ai_error}")
                    logger.info("🔄 Falling back to curated-only format")
                    step3_time = time.time() - step3_start
                    self.pipeline_stats['processing_times']['ai_processing'] = step3_time
                    website_articles = self._convert_curated_to_website_format(curated_articles)
                
            else:
                logger.info("⚠️ Real-time AI processing disabled - using basic format")
                # Convert curated articles to basic website format
                website_articles = self._convert_curated_to_website_format(curated_articles)
                step3_time = time.time() - step3_start
                self.pipeline_stats['processing_times']['format_conversion'] = step3_time
            
            # ✅ FIXED: Always ensure we have articles for website publication
            if not website_articles and curated_articles:
                logger.info("🔄 Creating fallback website articles from curated data")
                website_articles = self._convert_curated_to_website_format(curated_articles)
            
            if not website_articles:
                logger.warning("⚠️ No articles available for website publication")
                return self._create_pipeline_result(pipeline_id, "no_publishable_articles", start_time)
            
            # STEP 4: Website Publication
            logger.info("🌐 STEP 4: Publishing to Website...")
            step4_start = time.time()
            
            # Determine publication type based on what we have
            if ai_processed_articles and website_articles:
                # Use AI enhanced update method
                logger.info(f"📰 Publishing {len(website_articles)} AI-enhanced articles")
                self.website_updater.update_with_ai_enhanced_articles(website_articles)
                publication_result = {
                    'filename': 'current_articles.json',
                    'website_url': 'http://localhost:8003',
                    'update_type': 'ai_enhanced'
                }
            elif website_articles:
                # Use curated articles update method (fallback format)
                logger.info(f"📰 Publishing {len(website_articles)} curated articles (no AI enhancement)")
                self.website_updater.update_with_curated_articles(curated_articles)
                publication_result = {
                    'filename': 'current_articles.json', 
                    'website_url': 'http://localhost:8003',
                    'update_type': 'curated_only'
                }
            else:
                # Last resort: try to publish curated articles directly
                logger.warning("⚠️ No website articles available - attempting direct curated publication")
                self.website_updater.update_with_curated_articles(curated_articles)
                publication_result = {
                    'filename': 'current_articles.json', 
                    'website_url': 'http://localhost:8003',
                    'update_type': 'curated_fallback'
                }
            
            step4_time = time.time() - step4_start
            self.pipeline_stats['articles_published'] = len(website_articles) if website_articles else len(curated_articles)
            self.pipeline_stats['processing_times']['website_update'] = step4_time
            
            published_count = self.pipeline_stats['articles_published']
            logger.info(f"✅ Published {published_count} articles in {step4_time:.2f}s")
            
            # Calculate total pipeline time
            total_time = time.time() - start_time
            
            # Create success result
            result = self._create_pipeline_result(pipeline_id, "success", start_time)
            result.update({
                'website_url': publication_result.get('website_url', 'http://localhost:8003'),
                'live_articles_file': publication_result.get('filename'),
                'total_pipeline_time': total_time
            })
            
            logger.info(f"🎉 Pipeline {pipeline_id} completed successfully in {total_time:.2f}s")
            logger.info(f"📊 Final stats: {self.pipeline_stats['articles_scraped']} scraped → {self.pipeline_stats['articles_curated']} curated → {self.pipeline_stats['articles_ai_processed']} AI enhanced → {self.pipeline_stats['articles_published']} published")
            
            return result
            
        except Exception as e:
            error_msg = f"Pipeline {pipeline_id} failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.pipeline_stats['errors'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': error_msg,
                'step': 'pipeline_execution'
            })
            
            return self._create_pipeline_result(pipeline_id, "error", start_time, error_msg)
    
    def _convert_to_website_format(self, ai_articles: List[Any], source_type: str) -> List[Dict[str, Any]]:
        """Convert AI processed articles to website display format"""
        website_articles = []
        
        for article in ai_articles:
            # Convert ProcessedArticle dataclass to website format
            website_article = {
                'original_article_title': article.original_article_title,
                'simplified_english_title': article.simplified_english_title,
                'simplified_french_title': article.simplified_french_title,
                'english_summary': article.english_summary,
                'french_summary': article.french_summary,
                'original_article_link': article.original_article_link,
                'source_name': article.source_name,
                'published_date': article.original_article_published_date,
                'image_url': '',  # Will be added if available
                'quality_score': article.quality_scores.get('quality_score', 7.0),
                'relevance_score': article.quality_scores.get('relevance_score', 6.0),
                'importance_score': article.quality_scores.get('importance_score', 7.0),
                'total_score': article.quality_scores.get('total_score', 20.0),
                'breaking_news': False,  # Will be determined by scan type
                'urgency_score': 0.0,
                'contextual_title_explanations': article.contextual_title_explanations,
                'key_vocabulary': article.key_vocabulary,
                'cultural_context': article.cultural_context,
                'processed_at': article.processed_at,
                'processing_id': article.processing_id,
                'source_type': source_type
            }
            website_articles.append(website_article)
        
        return website_articles
    
    def _convert_curated_to_website_format(self, curated_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert curated articles to basic website format (fallback when AI processing is disabled)"""
        website_articles = []
        
        for article in curated_articles:
            # ✅ FIXED: Handle ScoredArticle objects properly
            if hasattr(article, 'original_data'):
                # ScoredArticle object
                original_data = article.original_data
                quality_score = article.quality_score
                relevance_score = article.relevance_score
                importance_score = article.importance_score
                total_score = article.total_score
                breaking_news = getattr(article, 'fast_tracked', False)
                urgency_score = 0.0  # Default for curated articles
            else:
                # Dictionary format (fallback)
                original_data = article.get('original_data', article)
                quality_score = article.get('quality_score', 7.0)
                relevance_score = article.get('relevance_score', 6.0)
                importance_score = article.get('importance_score', 7.0)
                total_score = article.get('total_score', 20.0)
                breaking_news = article.get('breaking_news', False)
                urgency_score = article.get('urgency_score', 0.0)
            
            website_article = {
                'original_article_title': original_data.get('title', ''),
                'simplified_english_title': original_data.get('title', ''),  # Same as original for now
                'simplified_french_title': original_data.get('title', ''),
                'english_summary': original_data.get('summary', ''),  # Will be English when AI processes it
                'french_summary': original_data.get('summary', ''),
                'original_article_link': original_data.get('link', ''),
                'source_name': original_data.get('source_name', ''),
                'published_date': original_data.get('published', ''),
                'image_url': original_data.get('image_url', ''),
                'quality_score': quality_score,
                'relevance_score': relevance_score,
                'importance_score': importance_score,
                'total_score': total_score,
                'breaking_news': breaking_news,
                'urgency_score': urgency_score,
                'contextual_title_explanations': [],  # Empty until AI processes
                'key_vocabulary': [],
                'cultural_context': {},
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'processing_id': f"curated_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'source_type': 'curated_only'
            }
            website_articles.append(website_article)
        
        return website_articles
    
    def _create_pipeline_result(self, pipeline_id: str, status: str, start_time: float, error_msg: str = None) -> Dict[str, Any]:
        """Create standardized pipeline result"""
        return {
            'pipeline_id': pipeline_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': status,
            'duration': time.time() - start_time,
            'statistics': self.pipeline_stats.copy(),
            'error': error_msg,
            'ai_processing_summary': self.ai_processor.get_processing_summary() if hasattr(self, 'ai_processor') else None
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'controller_status': 'active',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'configuration': {
                'ai_processing_enabled': self.config['cost']['enable_realtime_ai_processing'],
                'daily_ai_budget': self.config['cost']['daily_cost_limit'],
                'max_daily_articles': self.config['cost']['max_ai_articles_per_day']
            },
            'pipeline_statistics': self.pipeline_stats,
            'ai_processor_status': self.ai_processor.get_processing_summary(),
            'scraper_status': self.scraper.get_processing_stats(),
            'data_directory': self.data_dir,
            'website_status': 'running on localhost:8003'
        }

def main():
    """Main entry point for manual testing"""
    print("🚀 Better French Max - Automation Controller")
    print("=" * 50)
    
    try:
        controller = AutomationController()
        
        # Get system status
        status = controller.get_system_status()
        print(f"📊 System Status: {status['controller_status']}")
        print(f"🤖 AI Processing: {'✅ Enabled' if status['configuration']['ai_processing_enabled'] else '❌ Disabled'}")
        print(f"💰 Daily Budget: ${status['configuration']['daily_ai_budget']}")
        print("")
        
        # Ask user which type of scan to run
        print("Select scan type:")
        print("1. Breaking News Scan (urgent, 30min updates)")
        print("2. Regular Update Scan (comprehensive, 2hr updates)")
        print("3. System Status Only")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            result = controller.run_breaking_news_scan()
        elif choice == "2":
            result = controller.run_regular_update_scan()
        elif choice == "3":
            result = status
        else:
            print("❌ Invalid choice")
            return
        
        # Display results
        print("\n" + "=" * 50)
        print("📋 PIPELINE RESULTS:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Duration: {result.get('duration', 0):.2f}s")
        
        if 'statistics' in result:
            stats = result['statistics']
            print(f"Articles: {stats['articles_scraped']} scraped → {stats['articles_curated']} curated → {stats['articles_ai_processed']} AI enhanced → {stats['articles_published']} published")
        
        if result.get('status') == 'success':
            print(f"🌐 Website: {result.get('website_url', 'http://localhost:8003')}")
            print("✅ Pipeline completed successfully!")
        elif result.get('error'):
            print(f"❌ Error: {result['error']}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main() 