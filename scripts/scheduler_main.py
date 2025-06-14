#!/usr/bin/env python3
"""
Better French Max - Master Automation Scheduler
Orchestrates the complete automated news processing pipeline
Builds on proven manual system architecture with enterprise reliability
"""

import os
import sys
import time
import schedule
import logging
import json
import threading
import signal
from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from automation import AUTOMATION_CONFIG

# Set up logging
# Ensure logs directory exists
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, AUTOMATION_CONFIG['monitoring']['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'automation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterScheduler:
    """
    Master automation scheduler that orchestrates the entire pipeline
    Builds on proven manual system while adding enterprise automation
    """
    
    def __init__(self):
        self.config = AUTOMATION_CONFIG  # <-- Ensure config is set first!
        self.running = False
        self.threads = []
        self.last_health_check = None
        self.system_stats = {
            'start_time': datetime.now(timezone.utc),
            'articles_processed_today': 0,
            'ai_calls_used_today': 0,
            'cost_today': 0.0,
            'last_successful_update': None,
            'consecutive_failures': 0
        }
        
        # Import automation modules (created separately)
        self.smart_scraper = None
        self.quality_curator = None
        self.ai_processor = None
        self.website_updater = None
        self.monitor = None
        
        self.initialize_components()
        self.setup_signal_handlers()
        
    def initialize_components(self):
        """Initialize all automation components"""
        try:
            logger.info("🚀 Initializing Better French Max Automated System")
            logger.info(f"📊 Configuration: {AUTOMATION_CONFIG['meta']['system_name']}")
            logger.info(f"🔧 Based on: {AUTOMATION_CONFIG['meta']['based_on']}")
            
            # Import components (will be created in subsequent files)
            try:
                from smart_scraper import SmartScraper
                self.smart_scraper = SmartScraper()
                logger.info("✅ Smart Scraper initialized")
            except ImportError:
                logger.warning("⚠️ Smart Scraper not available yet")
            
            try:
                from quality_curator import AutomatedCurator
                self.quality_curator = AutomatedCurator()
                logger.info("✅ Quality Curator initialized")
            except ImportError:
                logger.warning("⚠️ Automated Curator not available yet")
            
            # Initialize AI processor if enabled
            if self.config['cost']['enable_realtime_ai_processing']:
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("AI_Engine", os.path.join(os.path.dirname(__file__), "AI-Engine.py"))
                    AI_Engine = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(AI_Engine)
                    CostOptimizedAIProcessor = AI_Engine.CostOptimizedAIProcessor
                    self.ai_processor = CostOptimizedAIProcessor()
                    logger.info("✅ AI processor enabled for automation")
                except ImportError as e:
                    logger.warning(f"⚠️ Could not load AI processor: {e}")
                    self.ai_processor = None
            else:
                logger.info("📊 AI processing disabled in configuration")
                self.ai_processor = None
            
            try:
                from website_updater import LiveWebsiteUpdater
                self.website_updater = LiveWebsiteUpdater()
                logger.info("✅ Website Updater initialized")
            except ImportError:
                logger.warning("⚠️ Website Updater not available yet")
            
            try:
                from monitoring import SystemMonitor
                self.monitor = SystemMonitor()
                logger.info("✅ System Monitor initialized")
            except ImportError:
                logger.warning("⚠️ System Monitor not available yet")
                
            logger.info("🎯 All available components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)
    
    def graceful_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"🛑 Received shutdown signal {signum}")
        self.stop()
    
    def setup_schedules(self):
        """Setup all automation schedules based on configuration"""
        config = AUTOMATION_CONFIG['scheduling']
        
        logger.info("📅 Setting up automation schedules:")
        
        # Breaking news monitoring (every 30 minutes)
        schedule.every(config['breaking_news_interval']).minutes.do(
            self.run_breaking_news_check
        )
        logger.info(f"   📰 Breaking news check: every {config['breaking_news_interval']} minutes")
        
        # Regular updates (every 2 hours during business hours)
        for hour in config['business_hours']:
            if hour % (config['regular_update_interval'] // 60) == 0:
                schedule.every().day.at(f"{hour:02d}:00").do(
                    self.run_regular_update
                )
        logger.info(f"   🔄 Regular updates: every {config['regular_update_interval']} minutes during business hours")
        
        # Daily AI processing (2 AM)
        schedule.every().day.at(config['ai_processing_time']).do(
            self.run_full_ai_processing
        )
        logger.info(f"   🤖 AI processing: daily at {config['ai_processing_time']}")
        
        # Website updates (every 5 minutes)
        schedule.every(config['website_update_interval']).minutes.do(
            self.update_website_if_needed
        )
        logger.info(f"   🌐 Website updates: every {config['website_update_interval']} minutes")
        
        # System health checks (every 10 minutes)
        health_interval = AUTOMATION_CONFIG['reliability']['health_check_interval']
        schedule.every(health_interval).minutes.do(
            self.run_health_check
        )
        logger.info(f"   🏥 Health checks: every {health_interval} minutes")
        
        # Daily cost and quality reporting
        schedule.every().day.at("23:55").do(
            self.generate_daily_report
        )
        logger.info("   📊 Daily reports: 23:55")
    
    def run_breaking_news_check(self):
        """Fast breaking news detection with immediate processing"""
        logger.info("🔥 Starting breaking news check with AI processing...")
        
        try:
            start_time = time.time()
            
            if not self.smart_scraper:
                logger.warning("⚠️ Smart scraper not available for breaking news")
                return
            
            # Breaking news scan (fast, focused on urgent content)
            breaking_keywords = AUTOMATION_CONFIG['scheduling']['breaking_news_keywords']
            breaking_articles = self.smart_scraper.quick_breaking_news_scan(breaking_keywords)
            
            if not breaking_articles:
                logger.info("📰 No breaking news detected")
                duration = time.time() - start_time
                logger.info(f"⚡ Breaking news check completed in {duration:.2f}s")
                return
            
            logger.info(f"🚨 Found {len(breaking_articles)} breaking news articles")
            
            # Fast-track quality curation for breaking news (lower threshold)
            if self.quality_curator:
                fast_tracked = self.quality_curator.fast_track_curation(breaking_articles)
                logger.info(f"⚡ {len(fast_tracked)} articles fast-tracked through curation")
                
                if fast_tracked:
                    # Convert ScoredArticle objects to dictionaries for AI processing
                    fast_tracked_dicts = []
                    for scored_article in fast_tracked:
                        if hasattr(scored_article, '__dict__'):
                            article_dict = {
                                'original_data': scored_article.original_data,
                                'quality_score': scored_article.quality_score,
                                'relevance_score': scored_article.relevance_score,
                                'importance_score': scored_article.importance_score,
                                'total_score': scored_article.total_score,
                                'curation_id': scored_article.curation_id,
                                'curated_at': scored_article.curated_at,
                                'fast_tracked': scored_article.fast_tracked,
                                'urgency_score': scored_article.urgency_score
                            }
                            fast_tracked_dicts.append(article_dict)
                    
                    # AI processing for breaking news (if enabled)
                    enhanced_articles = []
                    ai_success = False
                    
                    if (self.ai_processor and 
                        AUTOMATION_CONFIG['cost']['breaking_news_ai_enabled'] and 
                        self.check_cost_limits()):
                        
                        # Limit breaking news AI processing to top 5 articles (urgent focus)
                        max_breaking_ai = 5  # Smaller limit for breaking news to maintain speed
                        processing_batch = fast_tracked_dicts[:max_breaking_ai]
                        
                        logger.info(f"🚨 Rush AI processing for top {len(processing_batch)} breaking articles...")
                        try:
                            enhanced_articles = self.ai_processor.batch_process_articles(processing_batch)
                            if enhanced_articles:
                                ai_success = True
                                logger.info(f"⚡ Breaking news AI processing complete: {len(enhanced_articles)} articles")
                            else:
                                logger.warning("⚠️ Breaking news AI processing returned no results")
                        except Exception as ai_error:
                            logger.error(f"❌ Breaking news AI processing failed: {ai_error}")
                    
                    # Update website immediately
                    if self.website_updater:
                        if ai_success and enhanced_articles:
                            # Convert ProcessedArticle objects to dictionaries for website
                            enhanced_dicts = []
                            for article in enhanced_articles:
                                if hasattr(article, '__dict__'):
                                    enhanced_dicts.append(article.__dict__.copy())
                                else:
                                    enhanced_dicts.append(article)
                            
                            self.website_updater.update_with_ai_enhanced_articles(enhanced_dicts)
                            logger.info(f"🚨 Website updated with {len(enhanced_articles)} AI-enhanced breaking news")
                            # --- Fallback safeguard ---
                            # If the website currently has no data (e.g. first run or previous file deleted),
                            # publish the curated fast-tracked breaking articles so that the site is never empty.
                            try:
                                status = self.website_updater.get_website_status()
                                if status.get('total_articles', 0) == 0 and fast_tracked:
                                    self.website_updater.update_with_curated_articles(fast_tracked)
                                    logger.info(f"🚨 Fallback: Published {len(fast_tracked)} curated breaking news articles to prevent empty site")
                            except Exception as e:
                                logger.error(f"❌ Fallback publication for breaking news failed: {e}")
                        else:
                            # Skip publishing curated-only articles; keep existing website data unchanged
                            logger.info("🤖 AI enhancement unavailable; retaining existing published articles without adding curated-only items")
                            # --- Fallback safeguard ---
                            # If there is currently no website data (e.g. first deployment) publish curated
                            # articles anyway so the front-end has something to display.
                            try:
                                status = self.website_updater.get_website_status()
                                if status.get('total_articles', 0) == 0 and fast_tracked:
                            self.website_updater.update_with_curated_articles(fast_tracked)
                                    logger.info(f"🚨 Fallback: Published {len(fast_tracked)} curated breaking news articles to prevent empty site")
                            except Exception as e:
                                logger.error(f"❌ Fallback publication failed: {e}")
                    
                    self.system_stats['breaking_news_processed_today'] += len(fast_tracked)
                    self.system_stats['last_breaking_news'] = datetime.now(timezone.utc)
                    self.system_stats['consecutive_failures'] = 0
            
            duration = time.time() - start_time
            logger.info(f"⚡ Breaking news check completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Breaking news check failed: {e}")
            self.handle_component_failure('breaking_news', e)
    
    def run_regular_update(self):
        """Regular content scraping, curation, and AI processing for all quality articles"""
        logger.info("🔄 Starting regular content update with AI processing...")
        
        try:
            start_time = time.time()
            
            if not self.smart_scraper:
                logger.warning("⚠️ Smart scraper not available, attempting manual fallback")
                self.run_manual_fallback()
                return
            
            # Full scraping of all sources
            all_articles = self.smart_scraper.comprehensive_scrape()
            logger.info(f"📄 Scraped {len(all_articles)} articles from all sources")
            
            # Save daily articles archive (all unique articles)
            try:
                today = datetime.now(timezone.utc).date().isoformat()
                daily_file = f"data/live/raw_articles_{today}.json"
                os.makedirs(os.path.dirname(daily_file), exist_ok=True)
                
                # Convert NewsArticle objects to dict for JSON serialization
                daily_articles = []
                for article in all_articles:
                    if hasattr(article, '__dict__'):
                        article_dict = article.__dict__.copy()
                        article_dict['published_on_website'] = False  # Will update after processing
                        daily_articles.append(article_dict)
                
                with open(daily_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'date': today,
                        'total_articles': len(daily_articles),
                        'published_articles': [],
                        'unpublished_articles': daily_articles
                    }, f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"📁 Saved {len(daily_articles)} daily articles to {daily_file}")
            except Exception as e:
                logger.error(f"❌ Failed to save daily articles: {e}")
            
            # Quality curation with full scoring
            if self.quality_curator:
                curated_articles = self.quality_curator.full_curation(all_articles)
                logger.info(f"🎯 {len(curated_articles)} articles passed quality curation")
                
                # Convert ScoredArticle objects to dictionaries for AI processing
                curated_dicts = []
                for scored_article in curated_articles:
                    if hasattr(scored_article, '__dict__'):
                        article_dict = {
                            'original_data': scored_article.original_data,
                            'quality_score': scored_article.quality_score,
                            'relevance_score': scored_article.relevance_score,
                            'importance_score': scored_article.importance_score,
                            'total_score': scored_article.total_score,
                            'curation_id': scored_article.curation_id,
                            'curated_at': scored_article.curated_at,
                            'fast_tracked': scored_article.fast_tracked,
                            'urgency_score': scored_article.urgency_score
                        }
                        curated_dicts.append(article_dict)
                
                # Save curated articles
                try:
                    curated_file = f"data/live/curated_articles_{today}.json"
                    os.makedirs(os.path.dirname(curated_file), exist_ok=True)
                    with open(curated_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'date': today,
                            'curated_articles': curated_dicts,
                            'count': len(curated_dicts)
                        }, f, ensure_ascii=False, indent=2, default=str)
                    logger.info(f"📁 Saved {len(curated_dicts)} curated articles")
                except Exception as e:
                    logger.error(f"❌ Failed to save curated articles: {e}")
                
                # Try AI processing with proper data format
                ai_success = False
                enhanced_articles = []
                
                if (self.ai_processor and 
                    AUTOMATION_CONFIG['cost']['regular_updates_ai_enabled'] and 
                    self.check_cost_limits()):
                    
                    # Filter articles that meet AI processing threshold
                    ai_threshold = AUTOMATION_CONFIG['cost']['quality_threshold_for_ai']
                    ai_worthy_articles = [a for a in curated_dicts if a['total_score'] >= ai_threshold]
                    
                    if ai_worthy_articles:
                        max_for_ai = AUTOMATION_CONFIG['cost']['max_ai_articles_per_run']
                        processing_batch = ai_worthy_articles[:max_for_ai]
                        
                        logger.info(f"🤖 Processing top {len(processing_batch)} articles with AI (score >= {ai_threshold})")
                        try:
                            enhanced_articles = self.ai_processor.batch_process_articles(processing_batch)
                            if enhanced_articles:
                                ai_success = True
                                logger.info(f"✨ AI processing succeeded: {len(enhanced_articles)} articles enhanced")
                            else:
                                logger.warning("⚠️ AI processing returned no results")
                        except Exception as ai_error:
                            logger.error(f"❌ AI processing failed: {ai_error}")
                            enhanced_articles = []
                
                # Update website with best available content
                if self.website_updater:
                    if ai_success and enhanced_articles:
                        # Convert ProcessedArticle objects to dictionaries for website
                        enhanced_dicts = []
                        for article in enhanced_articles:
                            if hasattr(article, '__dict__'):
                                enhanced_dicts.append(article.__dict__.copy())
                            else:
                                enhanced_dicts.append(article)
                        
                        # Use AI-enhanced articles
                        self.website_updater.update_with_ai_enhanced_articles(enhanced_dicts)
                        logger.info(f"🌐 Website updated with {len(enhanced_articles)} AI-enhanced articles")
                        
                        # Update daily articles to mark AI-enhanced ones as published
                        try:
                            enhanced_links = {a.original_article_link for a in enhanced_articles}
                            for article in daily_articles:
                                if article.get('link') in enhanced_links:
                                    article['published_on_website'] = True
                        except Exception as e:
                            logger.debug(f"Could not update daily articles published status: {e}")
                    else:
                        # Skip publishing curated-only articles; keep existing website data unchanged
                        logger.info("🤖 AI enhancement unavailable; retaining existing published articles without adding curated-only items")
                        # --- Fallback safeguard ---
                        # If there is currently no website data (e.g. first deployment) publish curated
                        # articles anyway so the front-end has something to display.
                        try:
                            status = self.website_updater.get_website_status()
                            if status.get('total_articles', 0) == 0 and curated_articles:
                                self.website_updater.update_with_curated_articles(curated_articles)
                                logger.info(f"🌐 Fallback: Published {len(curated_articles)} curated articles to prevent empty site")
                        except Exception as e:
                            logger.error(f"❌ Fallback publication failed: {e}")
                
                # Update daily articles file with published status
                try:
                    published_articles = [a for a in daily_articles if a.get('published_on_website')]
                    unpublished_articles = [a for a in daily_articles if not a.get('published_on_website')]
                    
                    with open(daily_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'date': today,
                            'total_articles': len(daily_articles),
                            'published_articles': published_articles,
                            'unpublished_articles': unpublished_articles
                        }, f, ensure_ascii=False, indent=2, default=str)
                    logger.info(f"📁 Updated daily archive: {len(published_articles)} published, {len(unpublished_articles)} unpublished")
                except Exception as e:
                    logger.error(f"❌ Failed to update daily articles file: {e}")
                
                self.system_stats['articles_processed_today'] += len(curated_articles)
                self.system_stats['last_successful_update'] = datetime.now(timezone.utc)
                self.system_stats['consecutive_failures'] = 0
            
            duration = time.time() - start_time
            logger.info(f"✅ Regular update completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Regular update failed: {e}")
            self.handle_component_failure('regular_update', e)
    
    def run_full_ai_processing(self):
        """Daily AI enhancement for top articles (cost-optimized)"""
        logger.info("🤖 Starting daily AI processing...")
        
        try:
            start_time = time.time()
            
            # Check cost limits before processing
            if not self.check_cost_limits():
                logger.warning("💰 Daily cost limit reached, skipping AI processing")
                return
            
            if not self.ai_processor:
                logger.warning("⚠️ AI processor not available, serving curated articles only")
                return
            
            # Get top articles from today's curation
            top_articles = self.get_top_articles_for_ai_processing()
            
            if not top_articles:
                logger.info("📄 No articles available for AI processing")
                return
            
            max_articles = AUTOMATION_CONFIG['cost']['max_ai_articles_per_day']
            processing_batch = top_articles[:max_articles]
            
            logger.info(f"🎯 Processing {len(processing_batch)} top articles with AI")
            
            # Process in batches to avoid API rate limits
            enhanced_articles = self.ai_processor.batch_process_articles(processing_batch)
            
            if enhanced_articles:
                logger.info(f"✨ Successfully enhanced {len(enhanced_articles)} articles")
                
                # Update website with AI-enhanced content
                if self.website_updater:
                    self.website_updater.update_with_ai_enhanced_articles(enhanced_articles)
                    logger.info("🌐 Website updated with AI-enhanced articles")
                
                self.system_stats['ai_calls_used_today'] += len(enhanced_articles)
            
            duration = time.time() - start_time
            logger.info(f"🎉 AI processing completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")
            self.handle_component_failure('ai_processing', e)
    
    def update_website_if_needed(self):
        """Check if website needs updating and update if necessary"""
        try:
            if self.website_updater and self.website_updater.needs_update():
                self.website_updater.perform_incremental_update()
                logger.debug("🌐 Website incremental update completed")
        except Exception as e:
            logger.error(f"❌ Website update check failed: {e}")
    
    def run_health_check(self):
        """Comprehensive system health monitoring"""
        try:
            if self.monitor:
                health_status = self.monitor.check_system_health()
                
                if health_status['status'] == 'healthy':
                    logger.debug("💚 System health check: All systems operational")
                elif health_status['status'] == 'warning':
                    logger.warning(f"⚠️ System health warning: {health_status['issues']}")
                else:
                    logger.error(f"🔴 System health critical: {health_status['issues']}")
                    self.handle_critical_health_issues(health_status)
                
                self.last_health_check = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    def generate_daily_report(self):
        """Generate comprehensive daily performance report"""
        try:
            logger.info("📊 Generating daily performance report...")
            
            # Ensure logs directory exists
            logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            report = {
                'date': datetime.now(timezone.utc).date().isoformat(),
                'system_stats': self.system_stats.copy(),
                'uptime_hours': (datetime.now(timezone.utc) - self.system_stats['start_time']).total_seconds() / 3600,
                'cost_efficiency': self.calculate_cost_efficiency(),
                'quality_metrics': self.get_quality_metrics() if self.monitor else {},
                'recommendations': self.generate_recommendations()
            }
            
            # Save report
            report_path = os.path.join(logs_dir, f"daily_report_{report['date']}.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"📈 Daily report saved: {report_path}")
            
            # Reset daily counters
            self.reset_daily_counters()
            
        except Exception as e:
            logger.error(f"❌ Daily report generation failed: {e}")
    
    def check_cost_limits(self):
        """Check if we're within daily cost limits"""
        config = AUTOMATION_CONFIG['cost']
        
        if self.system_stats['cost_today'] >= config['daily_cost_limit']:
            return False
        
        if self.system_stats['ai_calls_used_today'] >= config['max_ai_calls_per_day']:
            return False
        
        return True
    
    def handle_component_failure(self, component_name, error):
        """Handle component failures with retry and fallback"""
        logger.error(f"Component '{component_name}' failed: {error}")
        self.system_stats['consecutive_failures'] += 1
        
        # Emergency stop if too many failures
        if self.system_stats['consecutive_failures'] >= AUTOMATION_CONFIG['reliability']['max_consecutive_failures']:
            logger.critical("🚨 EMERGENCY: Too many consecutive failures. Shutting down scheduler.")
            self.stop()
    
    def save_articles_for_ai_processing(self, articles):
        """Save high-quality articles for batch AI processing"""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            save_path = f"../data/live/curated_articles_{today}.json"
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': today,
                    'articles': articles,
                    'count': len(articles)
                }, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"   - Saved {len(articles)} articles to {save_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save articles for AI processing: {e}")
    
    def get_top_articles_for_ai_processing(self):
        """Get highest quality articles for AI enhancement"""
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            data_path = f"../data/live/curated_articles_{today}.json"
            
            if not os.path.exists(data_path):
                return []
            
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sort by total quality score (descending)
            articles = data.get('articles', [])
            sorted_articles = sorted(articles, 
                                   key=lambda x: x.get('total_score', 0), 
                                   reverse=True)
            
            return sorted_articles
            
        except Exception as e:
            logger.error(f"❌ Failed to get articles for AI processing: {e}")
            return []
    
    def calculate_cost_efficiency(self):
        """Calculate cost efficiency metrics"""
        try:
            if self.system_stats['ai_calls_used_today'] == 0:
                return {'efficiency': 'perfect', 'cost_per_article': 0}
            
            cost_per_article = self.system_stats['cost_today'] / self.system_stats['ai_calls_used_today']
            
            # Compare to manual system baseline
            manual_baseline = 1.0  # Assumed cost per article in manual system
            efficiency = ((manual_baseline - cost_per_article) / manual_baseline) * 100
            
            return {
                'efficiency_percentage': efficiency,
                'cost_per_article': cost_per_article,
                'total_cost_today': self.system_stats['cost_today'],
                'articles_processed': self.system_stats['ai_calls_used_today']
            }
            
        except Exception:
            return {'efficiency': 'unknown', 'error': 'calculation_failed'}
    
    def get_quality_metrics(self):
        """Get current quality metrics from monitor"""
        if self.monitor:
            return self.monitor.get_quality_summary()
        return {}
    
    def generate_recommendations(self):
        """Generate recommendations for system improvement"""
        return "System running nominally."
    
    def reset_daily_counters(self):
        """Reset daily counters for cost and processing"""
        logger.info("🗓️ Resetting daily counters")
        self.system_stats['articles_processed_today'] = 0
        self.system_stats['ai_calls_used_today'] = 0
        self.system_stats['cost_today'] = 0.0
        if self.ai_processor:
            self.ai_processor.reset_daily_counters()
    
    def start(self):
        """Start the scheduler"""
        logger.info("🚀 Starting Better French Max Automation System")
        logger.info(f"🎯 Key Features: {AUTOMATION_CONFIG['meta']['key_features']}")
        
        self.running = True
        self.setup_schedules()
        
        # Run initial health check
        self.run_health_check()
        
        logger.info("⚡ Automation scheduler started successfully")
        logger.info("📅 Schedule summary:")
        for job in schedule.jobs:
            logger.info(f"   {job}")
        
        # Main scheduler loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the automation scheduler gracefully"""
        logger.info("🛑 Stopping automation scheduler...")
        
        self.running = False
        
        # Wait for running threads to complete
        for thread in self.threads:
            thread.join(timeout=30)
        
        # Generate final report
        self.generate_daily_report()
        
        logger.info("✅ Automation scheduler stopped gracefully")

def main():
    """Main entry point for the automation system"""
    parser = argparse.ArgumentParser(description='Better French Max Automation Scheduler')
    parser.add_argument('--once', action='store_true', help='Run the main pipeline once and exit (for CI/CD)')
    args = parser.parse_args()
    try:
        # Validate configuration
        from automation import validate_configuration
        validation_result = validate_configuration()
        
        if validation_result != ["Configuration is valid"]:
            logger.error(f"❌ Configuration validation failed: {validation_result}")
            return
        
        logger.info("✅ Configuration validation passed")
        
        # Create scheduler
        scheduler = MasterScheduler()
        if args.once:
            logger.info("🔁 Running in one-shot mode for CI/CD (GitHub Actions)")
            scheduler.run_breaking_news_check()
            scheduler.run_regular_update()
            scheduler.update_website_if_needed()
            scheduler.generate_daily_report()
            logger.info("✅ One-shot pipeline complete. Exiting.")
        else:
            scheduler.start()
        
    except Exception as e:
        logger.error(f"❌ Failed to start automation system: {e}")
        raise

if __name__ == "__main__":
    main() 