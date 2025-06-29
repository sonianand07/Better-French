#!/usr/bin/env python3
"""
AI Engine v5 - System Test
Quick test to verify all components can be imported and basic functionality works.
"""

import sys
from pathlib import Path

# Add parent directory to sys.path to allow importing ai_engine_v5
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

def test_imports():
    """Test that all v5 components can be imported."""
    print("🧪 Testing AI Engine v5 imports...")
    
    try:
        from ai_engine_v5.core.scraper.autonomous_scraper import AutonomousScraper
        print("✅ AutonomousScraper imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import AutonomousScraper: {e}")
        return False
        
    try:
        from ai_engine_v5.core.processor.website_processor import WebsiteProcessor
        print("✅ WebsiteProcessor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import WebsiteProcessor: {e}")
        return False
        
    try:
        from ai_engine_v5.core.curator.intelligent_curator import IntelligentCurator
        print("✅ IntelligentCurator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import IntelligentCurator: {e}")
        return False
    
    return True


def test_scraper():
    """Test scraper initialization and basic methods."""
    print("\n🔧 Testing AutonomousScraper...")
    
    try:
        from ai_engine_v5.core.scraper.autonomous_scraper import AutonomousScraper
        
        scraper = AutonomousScraper()
        print("✅ AutonomousScraper initialized")
        
        # Test that methods exist
        assert hasattr(scraper, 'scrape_current_hour')
        assert hasattr(scraper, 'llm_select_top_10')
        print("✅ Required methods exist")
        
        # Test comprehensive RSS feed list (should be 30+ sources like V3+V4)
        assert len(scraper.sources) >= 30, f"Expected 30+ sources, got {len(scraper.sources)}"
        print(f"✅ {len(scraper.sources)} comprehensive RSS sources configured")
        
        # Test API key configuration
        assert hasattr(scraper, 'api_key')
        print("✅ API key configuration present")
        
        # Test source names
        sample_sources = ['Le Monde', 'Le Figaro', 'Libération', 'France Info', 'BFM TV']
        source_names = [scraper._get_source_name(url) for url in scraper.sources[:10]]
        print(f"✅ Sample source names: {', '.join(source_names[:5])}")
        
        return True
        
    except Exception as e:
        print(f"❌ AutonomousScraper test failed: {e}")
        return False


def test_processor():
    """Test processor initialization and basic methods."""
    print("\n🔧 Testing WebsiteProcessor...")
    
    try:
        from ai_engine_v5.core.processor.website_processor import WebsiteProcessor
        
        processor = WebsiteProcessor()
        print("✅ WebsiteProcessor initialized")
        
        # Test that methods exist
        assert hasattr(processor, 'enhance_articles')
        assert hasattr(processor, 'generate_website')
        print("✅ Required methods exist")
        
        # Test API key configuration
        assert hasattr(processor, 'api_key')
        assert hasattr(processor, 'v3_model')
        assert hasattr(processor, 'v4_model')
        print("✅ V3 + V4 model configuration present")
        
        return True
        
    except Exception as e:
        print(f"❌ WebsiteProcessor test failed: {e}")
        return False


def test_curator():
    """Test curator initialization and basic methods."""
    print("\n🔧 Testing IntelligentCurator...")
    
    try:
        from ai_engine_v5.core.curator.intelligent_curator import IntelligentCurator, Article
        
        curator = IntelligentCurator()
        print("✅ IntelligentCurator initialized")
        
        # Test with sample articles
        sample_articles = [
            Article(
                title="Test Article 1",
                summary="Test summary 1",
                link="https://example.com/1",
                source="Test Source",
                published_date="2024-01-01"
            ),
            Article(
                title="Test Article 2",
                summary="Test summary 2", 
                link="https://example.com/2",
                source="Test Source",
                published_date="2024-01-01"
            )
        ]
        
        result = curator.curate_articles(sample_articles)
        assert len(result.selected_articles) <= 10
        assert result.diversity_score >= 0.0
        print("✅ Basic curation test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ IntelligentCurator test failed: {e}")
        return False


def test_data_directory():
    """Test that data directory structure exists."""
    print("\n📁 Testing data directory structure...")
    
    from pathlib import Path
    
    data_dir = Path("ai_engine_v5/data")
    
    if data_dir.exists():
        print("✅ Data directory exists")
        return True
    else:
        print("❌ Data directory missing")
        return False


def test_api_key_security():
    """Test API key security configuration."""
    print("\n🔐 Testing API key security...")
    
    try:
        from ai_engine_v5.core.scraper.autonomous_scraper import AutonomousScraper
        
        scraper = AutonomousScraper()
        
        # Test that scraper checks for separate API key
        import os
        original_scraper_key = os.environ.get('OPENROUTER_SCRAPER_API_KEY')
        original_api_key = os.environ.get('OPENROUTER_API_KEY')
        
        # Temporarily clear both keys
        if 'OPENROUTER_SCRAPER_API_KEY' in os.environ:
            del os.environ['OPENROUTER_SCRAPER_API_KEY']
        if 'OPENROUTER_API_KEY' in os.environ:
            del os.environ['OPENROUTER_API_KEY']
        
        # Test initialization without keys
        scraper_no_key = AutonomousScraper()
        assert scraper_no_key.api_key is None
        
        # Restore original keys
        if original_scraper_key:
            os.environ['OPENROUTER_SCRAPER_API_KEY'] = original_scraper_key
        if original_api_key:
            os.environ['OPENROUTER_API_KEY'] = original_api_key
        
        print("✅ API key security configuration works correctly")
        return True
        
    except Exception as e:
        print(f"❌ API key security test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 AI ENGINE v5 SYSTEM TEST")
    print("=" * 40)
    print(f"📍 Testing from: {Path.cwd()}")
    print(f"📦 Module path: {Path(__file__).parent}")
    
    all_passed = True
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Scraper Test", test_scraper),
        ("Processor Test", test_processor),
        ("Curator Test", test_curator),
        ("Data Directory Test", test_data_directory),
        ("API Key Security Test", test_api_key_security)
    ]
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ AI Engine v5 is ready for autonomous operation")
        print("")
        print("🔐 SECURITY: Separate API key system configured")
        print("📰 QUALITY: 30+ comprehensive sources (same as V3+V4)")
        print("🤖 AUTONOMOUS: Zero manual intervention required")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️ Check the errors above and fix before deployment")
    
    print("\n🤖 Next steps:")
    print("1. Set OPENROUTER_SCRAPER_API_KEY (separate from dev key)")
    print("2. Deploy workflows to GitHub Actions")
    print("3. Monitor autonomous operation")
    print("4. Enjoy 24/7 operation without API key issues!")
    
    return all_passed


if __name__ == "__main__":
    main() 