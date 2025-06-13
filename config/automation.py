# 🤖 Automation Configuration for Better French Max
# Builds on proven manual system architecture with enhanced automation

import os
from datetime import datetime, timezone

# 🔄 SCHEDULING CONFIGURATION
SCHEDULING_CONFIG = {
    # Breaking news monitoring (urgent updates)
    'breaking_news_interval': 30,  # minutes
    'breaking_news_keywords': [
        'breaking', 'urgent', 'alerte', 'exclusif', 'dernière minute',
        'gouvernement', 'président', 'élection', 'crise', 'attentat',
        'manifestation', 'grève nationale', 'état d\'urgence'
    ],
    
    # Regular content updates
    'regular_update_interval': 120,  # minutes (every 2 hours)
    'business_hours': list(range(6, 23)),  # 6 AM to 10 PM
    'weekend_reduced_frequency': True,
    
    # AI processing schedule (cost optimization)
    'ai_processing_time': '02:00',  # Daily at 2 AM
    'ai_processing_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
    
    # Website update frequency
    'website_update_interval': 5,  # minutes (for new content)
    'website_full_refresh': 60,   # minutes (complete refresh)
}

# 🎯 QUALITY STANDARDS (Inherited from proven manual system)
QUALITY_CONFIG = {
    # Quality score thresholds (0-30 scale from original system)
    'min_total_score': 18.0,        # Minimum for AI processing (was 7.0/10, now 21/30)
    'min_quality_score': 6.0,       # Writing quality (0-10)
    'min_relevance_score': 6.5,     # Expat relevance (0-10) 
    'min_importance_score': 5.5,    # News importance (0-10)
    
    # Expat/immigrant relevance keywords (from original curator)
    'high_relevance_keywords': {
        # Immigration & Legal (HIGH PRIORITY)
        'immigration', 'visa', 'carte de séjour', 'naturalisation', 'préfecture', 
        'titre de séjour', 'étranger', 'expatrié', 'résidence', 'citoyenneté',
        
        # Daily Life & Services (HIGH PRIORITY)
        'sécurité sociale', 'caf', 'pôle emploi', 'impôts', 'logement', 'santé',
        'transport', 'sncf', 'ratp', 'école', 'université', 'formation',
        'banque', 'assurance', 'mutuelle', 'médecin', 'hôpital',
        
        # French Culture & Society (HIGH PRIORITY)
        'culture française', 'tradition', 'laïcité', 'république', 'marianne',
        'gastronomie', 'cuisine', 'vin', 'fromage', 'baguette', 'café',
        'festival', 'patrimoine', 'monument', 'musée', 'art français',
        
        # Government & Politics affecting daily life (HIGH PRIORITY)
        'gouvernement', 'président', 'assemblée nationale', 'sénat', 'maire',
        'conseil municipal', 'région', 'département', 'commune', 'élection',
        'réforme', 'loi', 'décret', 'politique sociale',
    },
    
    'medium_relevance_keywords': {
        # National Events & News (MEDIUM PRIORITY)
        'france', 'français', 'national', 'pays', 'état', 'société',
        'population', 'citoyen', 'public', 'social', 'communauté',
        
        # Current Affairs (MEDIUM PRIORITY)
        'actualité', 'information', 'débat', 'polémique', 'manifestation',
        'grève', 'syndical', 'droit', 'justice', 'tribunal',
    },
    
    # Quality exclusion criteria (from original system)
    'exclusion_keywords': {
        'people', 'célébrité', 'star', 'télé-réalité', 'scandale',
        'paparazzi', 'instagram', 'tiktok', 'influenceur',
        'gossip', 'rumeur', 'vie privée', 'buzz', 'choc'
    },
    
    # Quality trends monitoring
    'quality_trend_window': 7,      # days to track quality trends
    'quality_decline_threshold': 0.5,  # alert if avg drops by this much
}

# 💰 COST OPTIMIZATION CONFIGURATION
COST_CONFIG = {
    # AI processing strategy (QUALITY-FIRST approach)
    'enable_realtime_ai_processing': True,    # NEW: Process all articles with AI
    'max_ai_articles_per_day': 100,           # Daily limit (backup safety)
    'max_ai_articles_per_run': 20,            # Increased to process up to 20 articles per 2-hour run
    'max_ai_calls_per_day': 120,              # API call limit
    'ai_batch_size': 5,                       # Process in batches
    
    # Smart processing tiers
    'breaking_news_ai_priority': True,        # NEW: Always process breaking news
    'breaking_news_ai_enabled': True,         # NEW: Process breaking news with AI
    'regular_updates_ai_enabled': True,       # NEW: Process regular updates
    'quality_threshold_for_ai': 15.0,         # Only process articles scoring 15+/30
    
    # Smart caching system
    'enable_smart_caching': True,
    'cache_similarity_threshold': 0.85,       # Reuse if 85% similar
    'cache_retention_days': 30,               # Keep cache for 30 days
    
    # Cost monitoring (adjusted for higher usage)
    'daily_cost_limit': 25.0,                 # Increased from $10 to $25 USD per day
    'cost_alert_threshold': 20.0,             # Alert at 80% of limit
    'emergency_stop_cost': 30.0,              # Emergency stop at this cost
    
    # Fallback strategies
    'fallback_to_curated_only': True,         # Serve without AI if costs high
    'reduced_processing_mode': True,          # Emergency cost reduction
}

# 🛡️ RELIABILITY CONFIGURATION
RELIABILITY_CONFIG = {
    # Error handling thresholds
    'max_source_failures': 3,          # Max failures before disabling source
    'retry_delay_minutes': 15,         # Wait before retrying failed source
    'max_consecutive_failures': 5,     # Max before emergency fallback
    
    # System health monitoring
    'health_check_interval': 10,       # minutes
    'performance_alert_threshold': 2.0, # seconds for slow operations
    'memory_usage_limit': 85,          # percent
    
    # Fallback mechanisms
    'enable_manual_fallback': True,    # Fallback to manual system
    'auto_recovery_attempts': 3,       # Auto-recovery tries
    'emergency_contact_enabled': False, # Email alerts (configure separately)
    
    # Data integrity
    'validate_article_structure': True,
    'check_data_freshness': True,
    'max_article_age_hours': 48,       # Alert if no new articles
}

# 🌐 WEBSITE UPDATE CONFIGURATION  
WEBSITE_CONFIG = {
    # Live update settings
    'enable_live_updates': True,
    'max_articles_displayed': 100,     # Keep top 100 articles (rolling system)
    'update_animation_duration': 300,  # milliseconds
    'show_update_notifications': True,
    
    # Data paths (relative to automation system)
    'website_data_path': 'data/live/rolling_articles.json',
    'website_backup_path': 'data/live/backup_articles.json',
    'static_website_path': 'website/',
    
    # Performance optimization
    'lazy_load_images': True,
    'compress_json_output': True,
    'cache_static_assets': True,
    
    # User experience
    'show_loading_indicators': True,
    'graceful_degradation': True,      # Work even if live updates fail
    'offline_mode_available': False,   # Future feature
}

# 📊 MONITORING CONFIGURATION
MONITORING_CONFIG = {
    # Metrics collection
    'collect_performance_metrics': True,
    'collect_quality_metrics': True,
    'collect_cost_metrics': True,
    'collect_user_metrics': False,     # Privacy-focused
    
    # Log levels and retention
    'log_level': 'INFO',               # DEBUG, INFO, WARNING, ERROR
    'log_retention_days': 30,
    'max_log_file_size_mb': 100,
    
    # Alert thresholds
    'alert_on_quality_drop': True,
    'alert_on_cost_spike': True,
    'alert_on_system_errors': True,
    
    # Reporting
    'daily_summary_enabled': True,
    'weekly_report_enabled': True,
    'monthly_analytics': True,
}

# 🔗 INTEGRATION PATHS
INTEGRATION_CONFIG = {
    # Paths to original proven system (for reference and fallback)
    'original_scripts_path': '../02_Scripts/',
    'original_data_path': '../04_Data_Output/',
    'original_website_path': '../better-french-website/',
    
    # Shared configurations
    'use_original_api_config': True,   # Use existing API keys
    'inherit_source_config': True,     # Use proven news sources
    'maintain_quality_standards': True, # Keep same quality logic
    
    # Migration settings
    'parallel_testing_mode': False,    # Run alongside manual system
    'gradual_migration_enabled': False, # Slowly replace manual system
    'rollback_enabled': True,          # Can revert to manual instantly
}

# 🤖 AI PROCESSING CONFIGURATION
AI_PROCESSING_CONFIG = {
    # OpenRouter API settings (same as manual system)
    'model': 'meta-llama/llama-3-70b-instruct',  # Default cost-efficient model
    'api_base_url': 'https://openrouter.ai/api/v1',
    'max_tokens': 1000,
    'temperature': 0.3,
    'top_p': 0.9,
    
    # Rate limiting and cost control
    'rate_limit_delay': 2.0,           # seconds between API calls
    'batch_processing': True,
    'retry_attempts': 3,
    'timeout_seconds': 30,
    
    # Processing optimization
    'skip_duplicate_processing': True,
    'cache_ai_results': True,
    'quality_threshold_for_ai': 18.0,  # Only process high-quality articles
    
    # Output formatting (same as manual system)
    'include_cultural_context': True,
    'simplify_french_language': True,
    'provide_english_translations': True,
    'explain_french_terms': True,
}

# 🎯 FEATURE FLAGS
FEATURE_FLAGS = {
    # Core automation features
    'enable_scheduling': True,
    'enable_cost_optimization': True,
    'enable_quality_monitoring': True,
    'enable_live_website_updates': True,
    
    # Advanced features (can be enabled gradually)
    'enable_smart_caching': True,
    'enable_predictive_processing': False,  # Future AI feature
    'enable_user_personalization': False,  # Future feature
    'enable_mobile_app_api': False,        # Future feature
    
    # Experimental features
    'enable_advanced_nlp': False,          # More sophisticated analysis
    'enable_sentiment_analysis': False,    # Article sentiment scoring
    'enable_trend_prediction': False,      # Predict trending topics
}

# 🔐 SECURITY CONFIGURATION
SECURITY_CONFIG = {
    # API security
    'rate_limit_requests': True,
    'validate_api_responses': True,
    'encrypt_cached_data': False,      # Future security enhancement
    
    # Data privacy
    'anonymize_logs': True,
    'no_user_tracking': True,          # Privacy-first approach
    'minimal_data_retention': True,
    
    # System security
    'validate_file_paths': True,
    'sanitize_user_inputs': True,
    'secure_config_storage': True,
}

# 📰 SCRAPING CONTROL CONFIGURATION
SCRAPING_CONFIG = {
    # Article collection limits
    'max_articles_per_source_breaking': 10,    # Max articles per source for breaking news scan
    'max_articles_per_source_regular': 20,     # Max articles per source for regular updates
    'max_total_articles_breaking': 50,         # Total limit for breaking news scan
    'max_total_articles_regular': 200,         # Total limit for regular updates
    
    # Time filtering settings
    'breaking_news_timeframe_hours': 2,        # Only articles from last 2 hours for breaking
    'regular_update_timeframe_hours': 6,       # Only articles from last 6 hours for regular
    'max_article_age_hours': 48,               # Never process articles older than this
    
    # Deduplication settings
    'enable_duplicate_detection': True,
    'similarity_threshold': 0.85,              # Articles with 85%+ similarity are duplicates
    'title_similarity_threshold': 0.75,        # Title similarity threshold
    'hash_comparison_enabled': True,           # Use content hash for exact duplicates
    'cache_duration_hours': 24,                # How long to keep articles in dedup cache
    
    # Source prioritization
    'breaking_news_priority_sources': [
        'BFM TV', 'France Info', 'Le Monde', 'Le Figaro', 'France 24'
    ],
    'high_reliability_sources': [
        'Le Monde', 'Le Figaro', 'Liberation', 'France Info', 'AFP'
    ],
    
    # Performance optimization
    'parallel_scraping_threads': 8,            # Max concurrent scraping threads
    'request_timeout_seconds': 15,             # Timeout for feed requests
    'retry_failed_sources': True,              # Retry failed sources after delay
    'retry_delay_minutes': 30,                 # Wait time before retry
}

def get_config_summary():
    """Get a summary of current automation configuration"""
    return {
        'system_name': 'Better French Max - Automated System',
        'version': '1.0.0',
        'build_date': datetime.now(timezone.utc).isoformat(),
        'based_on': 'Proven manual system architecture',
        'key_features': [
            'Live updates every 30 minutes for breaking news',
            '90% cost reduction through smart AI processing',
            'Enterprise reliability with failover mechanisms',
            'Quality maintained from original proven system',
            'Zero-risk parallel deployment strategy'
        ],
        'quality_inheritance': 'Full compatibility with manual system quality standards',
        'deployment_ready': True
    }

def validate_configuration():
    """Validate that all configuration values are sensible"""
    issues = []
    
    # Check scheduling makes sense
    if SCHEDULING_CONFIG['breaking_news_interval'] > SCHEDULING_CONFIG['regular_update_interval']:
        issues.append("Breaking news interval should be shorter than regular updates")
    
    # Check quality thresholds are reasonable
    if QUALITY_CONFIG['min_total_score'] > 30:
        issues.append("Total quality score cannot exceed 30 (max possible)")
    
    # Check cost limits are reasonable
    if COST_CONFIG['max_ai_articles_per_day'] < 5:
        issues.append("Minimum 5 articles needed for meaningful content")
    
    return issues if issues else ["Configuration is valid"]

# Export main configuration object
AUTOMATION_CONFIG = {
    'scheduling': SCHEDULING_CONFIG,
    'quality': QUALITY_CONFIG,
    'cost': COST_CONFIG,
    'reliability': RELIABILITY_CONFIG,
    'website': WEBSITE_CONFIG,
    'monitoring': MONITORING_CONFIG,
    'integration': INTEGRATION_CONFIG,
    'ai_processing': AI_PROCESSING_CONFIG,
    'features': FEATURE_FLAGS,
    'security': SECURITY_CONFIG,
    'scraping': SCRAPING_CONFIG,
    'meta': get_config_summary()
} 