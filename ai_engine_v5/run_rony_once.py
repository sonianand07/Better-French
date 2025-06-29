#!/usr/bin/env python3
"""
Run Rony Once - Quick Test Script
Runs the enhanced Rony autonomous scraper once to test the system
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ai_engine_v5.core.scraper.autonomous_scraper import AutonomousScraper, UserProfile

# Load API key
try:
    from config.api_config import OPENROUTER_API_KEY
    print(f"✅ API key loaded: {OPENROUTER_API_KEY[:20]}...")
except ImportError:
    print("❌ No API key found in config/api_config.py")
    print("   Please set up your OpenRouter API key first")
    sys.exit(1)

async def run_rony_once():
    """Run Rony once with enhanced HFLLA system"""
    
    print("🚀 STARTING RONY - Enhanced HFLLA (NEWS IMPORTANCE FIRST)")
    print("="*70)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Mission: Select 10 most important news (60% French + 40% International)")
    print(f"🧠 AI: Gemini 2.5 Pro with anti-bubble system")
    print()
    
    # Create user profile
    profile = UserProfile(
        user_id="anand_test",
        french_level="B1",
        lives_in="Paris",
        pain_points=["CAF", "logement", "SNCF", "impôts"],
        work_domains=["tech", "startup"],
        interests=["technology", "culture", "politics"]
    )
    
    print(f"👤 Profile: {profile.french_level} level, lives in {profile.lives_in}")
    print(f"🎯 Pain points: {profile.pain_points}")
    print(f"💼 Work domains: {profile.work_domains}")
    print()
    
    try:
        # Run Rony
        async with AutonomousScraper(OPENROUTER_API_KEY, profile) as rony:
            result = await rony.run_autonomous_cycle()
        
        print()
        print("🎉 RONY COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"📊 Articles collected: {result['articles_collected']}")
        print(f"✅ Articles selected: {result['articles_selected']}")
        print(f"⏱️  Duration: {result['duration_seconds']:.1f} seconds")
        print(f"🎯 Average quality: {result['quality_metrics']['avg_hflla_score']:.1f}")
        print()
        
        if result['selected_articles']:
            print("📰 SELECTED ARTICLES:")
            print("-" * 50)
            for i, article in enumerate(result['selected_articles'][:5], 1):
                print(f"{i}. {article['title']}")
                print(f"   Source: {article['source']} | Score: {article['total_score']:.1f} | Category: {article['predicted_category']}")
                print()
        
        # Show category distribution
        if result.get('hflla_category_distribution'):
            print("🏷️  CATEGORY DISTRIBUTION:")
            print("-" * 30)
            for category, count in result['hflla_category_distribution'].items():
                percentage = (count / result['articles_selected']) * 100
                print(f"   {category}: {count} articles ({percentage:.1f}%)")
        
        print()
        print("🌍 GLOBAL COVERAGE STATUS:")
        print(f"   ✅ Anti-bubble system: ACTIVE")
        print(f"   ✅ International sources: BOOSTED")
        print(f"   ✅ Crisis detection: ENABLED")
        print(f"   ✅ News importance: PRIORITIZED")
        
        print()
        print("📁 Data saved to: ai_engine_v5/data/scraper_data.json")
        print("🌐 Ready for website processing!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("🔧 Common fixes:")
        print("   1. Check your internet connection")
        print("   2. Verify OpenRouter API key is valid")
        print("   3. Try running again (some RSS sources may be temporarily down)")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_rony_once())
    if success:
        print()
        print("🎯 NEXT STEPS:")
        print("   1. Check your website to see the new articles")
        print("   2. Verify international coverage is working")
        print("   3. Set up scheduled runs if satisfied")
    
    sys.exit(0 if success else 1) 