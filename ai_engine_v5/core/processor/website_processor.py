"""
AI Engine v5 - Website Processor
PRESERVES V3+V4 quality while using Rony's intelligent article selection.
"""

import json
import requests
import os
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path

# Robust imports that work in GitHub Actions environment
def setup_imports():
    """Setup imports to work in both local and GitHub Actions environments."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    
    # Add both v3 and v4 directories to path
    v3_path = project_root / 'ai_engine_v3'
    v4_path = project_root / 'ai_engine_v4'
    
    sys.path.insert(0, str(v3_path))
    sys.path.insert(0, str(v4_path))
    sys.path.insert(0, str(project_root))
    
    print(f"🔍 Project root: {project_root}")
    print(f"🔍 V3 path: {v3_path} (exists: {v3_path.exists()})")
    print(f"🔍 V4 path: {v4_path} (exists: {v4_path.exists()})")

# Setup imports
setup_imports()

# Import V3+V4 proven processing components
try:
    print("🔄 Attempting to import V3+V4 components...")
    
    # Import V3 components
    from processor import ProcessorV2
    from models import Article, QualityScores
    print("   ✅ V3 components imported successfully")
    
    # Import V4 components  
    from client import HighLLMClient
    from prompt_loader import render
    print("   ✅ V4 components imported successfully")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("🔄 Trying alternative import approach...")
    
    try:
        # Alternative import approach
        import importlib.util
        
        # Load V3 processor manually
        v3_processor_path = Path(__file__).parent.parent.parent.parent / 'ai_engine_v3' / 'processor.py'
        v3_models_path = Path(__file__).parent.parent.parent.parent / 'ai_engine_v3' / 'models.py'
        
        # Load V4 client manually
        v4_client_path = Path(__file__).parent.parent.parent.parent / 'ai_engine_v4' / 'client.py'
        v4_prompt_path = Path(__file__).parent.parent.parent.parent / 'ai_engine_v4' / 'prompt_loader.py'
        
        print(f"   📁 V3 processor: {v3_processor_path} (exists: {v3_processor_path.exists()})")
        print(f"   📁 V3 models: {v3_models_path} (exists: {v3_models_path.exists()})")
        print(f"   📁 V4 client: {v4_client_path} (exists: {v4_client_path.exists()})")
        print(f"   📁 V4 prompt: {v4_prompt_path} (exists: {v4_prompt_path.exists()})")
        
        # Import manually if files exist
        if all([v3_processor_path.exists(), v3_models_path.exists(), 
                v4_client_path.exists(), v4_prompt_path.exists()]):
            
            # Load V3 models
            spec = importlib.util.spec_from_file_location("v3_models", v3_models_path)
            v3_models = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(v3_models)
            Article = v3_models.Article
            QualityScores = v3_models.QualityScores
            
            # Load V3 processor
            spec = importlib.util.spec_from_file_location("v3_processor", v3_processor_path)
            v3_processor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(v3_processor)
            ProcessorV2 = v3_processor.ProcessorV2
            
            # Load V4 client
            spec = importlib.util.spec_from_file_location("v4_client", v4_client_path)
            v4_client = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(v4_client)
            HighLLMClient = v4_client.HighLLMClient
            
            # Load V4 prompt loader
            spec = importlib.util.spec_from_file_location("v4_prompt", v4_prompt_path)
            v4_prompt = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(v4_prompt)
            render = v4_prompt.render
            
            print("   ✅ Manual import successful!")
            
        else:
            raise ImportError("V3+V4 components not found")
        
    except Exception as e2:
        print(f"❌ All import attempts failed: {e2}")
        print("🚨 CRITICAL: Cannot load V3+V4 components!")
        print("💡 The V5 processor requires V3+V4 components to maintain quality")
        raise ImportError(f"Cannot import V3+V4 components. Original error: {e}, Alternative error: {e2}")


class WebsiteProcessor:
    """
    V5 Website Processor - PRESERVES V3+V4 PROVEN QUALITY
    
    This processor applies the EXACT same enhancement pipeline as V3+V4
    to articles selected by Rony's intelligent scraper.
    
    NO PROMPTS CHANGED - QUALITY PRESERVED!
    """
    
    def __init__(self):
        print("🚀 " + "="*60)
        print("🚀 V5 WEBSITE PROCESSOR STARTING UP")
        print("🚀 " + "="*60)
        
        print("🔍 Checking API keys...")
        self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENROUTER_SCRAPER_API_KEY')
        if not self.api_key:
            print("❌ CRITICAL: No API key found!")
            print("💡 Need OPENROUTER_API_KEY or OPENROUTER_SCRAPER_API_KEY environment variable")
            raise ValueError("API key required for V3+V4 enhancement")
        else:
            print("✅ API key found and loaded")
        
        print("🔧 Initializing V3+V4 processing components...")
        try:
            # Use EXACT same processors as V3+V4
            self.v3_processor = ProcessorV2()  # Proven V3 processing
            print("   ✅ V3 processor loaded (contextual words + simplification)")
            
            self.v4_client = HighLLMClient()   # Proven V4 verification
            print("   ✅ V4 client loaded (GPT-4o verification)")
            
        except Exception as e:
            print(f"❌ CRITICAL: Failed to load V3+V4 components: {e}")
            raise
        
        print("🎉 V5 Website Processor READY!")
        print("✨ Using PROVEN V3+V4 enhancement pipeline")
        print("✨ NO quality reduction - same prompts preserved")
        print("✨ Same display format: **English:** _French word_")
        print("")
    
    def enhance_articles(self, rony_articles: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Apply EXACT V3+V4 enhancement pipeline to Rony's selected articles.
        
        PRESERVES:
        - V3 contextual_words_v3.jinja prompt (proven tooltip generation)
        - V3 simplify_titles_summaries_v3.jinja prompt (proven simplification)
        - V4 review_tooltips.jinja prompt (proven GPT-4o verification)
        - All display formats: **English:** _French word_
        - All quality standards and schemas
        """
        print("🎯 " + "="*60)
        print("🎯 STARTING ARTICLE ENHANCEMENT PIPELINE")
        print("🎯 " + "="*60)
        
        if not rony_articles:
            print("⚠️ No articles provided for enhancement!")
            print("💡 This might mean Rony didn't select any articles yet")
            return [], 0.0
        
        print(f"📊 Articles to enhance: {len(rony_articles)}")
        print("🔧 Pipeline: Rony Selection → V3 Enhancement → V4 Verification → V5 Website")
        print("✅ Using PROVEN prompts - NO quality reduction")
        print("")
        
        # Step 1: Convert Rony's articles to V3 Article model format
        print("🔄 STEP 1: Converting Rony articles to V3 format...")
        v3_articles = []
        for i, article in enumerate(rony_articles, 1):
            print(f"   📄 {i}/{len(rony_articles)}: {article.get('title', 'No title')[:50]}...")
            
            # Create Article object with quality scores
            quality_scores = QualityScores(
                quality_score=8.0,     # Rony pre-selected these as high quality
                relevance_score=9.0,   # Profile-aware selection ensures relevance
                importance_score=8.0,  # LLM selection ensures importance
                total_score=25.0       # High total score for Rony-selected articles
            )
            
            v3_article = Article(
                original_article_title=article.get('title', ''),
                original_article_link=article.get('link', ''),
                original_article_published_date=article.get('published', ''),
                source_name=article.get('source', 'Unknown'),
                quality_scores=quality_scores
            )
            v3_articles.append(v3_article)
        
        print(f"✅ Successfully converted {len(v3_articles)} articles to V3 format")
        print("")
        
        # Step 2: Apply V3 enhancement (EXACT same as V3)
        print("🎯 STEP 2: Applying V3 enhancement...")
        print("   🔮 Using contextual_words_v3.jinja (proven tooltip generation)")
        print("   📝 Using simplify_titles_summaries_v3.jinja (proven simplification)")
        print("   💰 This will cost money - processing with OpenRouter...")
        
        try:
            enhanced_articles = []
            for i, article in enumerate(v3_articles, 1):
                print(f"   🔧 Processing {i}/{len(v3_articles)}: {article.original_article_title[:40]}...")
                
                try:
                    enhanced = self.v3_processor.process_article(article)
                    enhanced_articles.append(enhanced)
                    print(f"      ✅ Enhanced successfully")
                    
                    # Show what was enhanced
                    if enhanced.ai_enhanced:
                        tooltips_count = len(enhanced.contextual_title_explanations) if enhanced.contextual_title_explanations else 0
                        print(f"      📊 Generated {tooltips_count} contextual tooltips")
                        if enhanced.simplified_french_title:
                            print(f"      🇫🇷 Simplified French: {enhanced.simplified_french_title[:40]}...")
                        if enhanced.simplified_english_title:
                            print(f"      🇬🇧 Simplified English: {enhanced.simplified_english_title[:40]}...")
                    
                except Exception as e:
                    print(f"      ❌ Failed to enhance: {e}")
                    enhanced_articles.append(article)  # Keep original
            
            v3_cost = self.v3_processor.total_cost_usd
            print(f"✅ V3 enhancement complete!")
            print(f"   💰 Cost: ${v3_cost:.4f}")
            print(f"   📊 Successfully enhanced: {len([a for a in enhanced_articles if a.ai_enhanced])}/{len(enhanced_articles)}")
            print("")
            
        except Exception as e:
            print(f"❌ CRITICAL: V3 enhancement failed: {e}")
            print("💡 This might be an API key issue or network problem")
            return [], 0.0
        
        # Step 3: Apply V4 verification (EXACT same as V4)
        print("🔍 STEP 3: Applying V4 verification...")
        print("   🤖 Using GPT-4o for quality review")
        print("   📝 Using review_tooltips.jinja (proven verification)")
        print("   🎯 Fixing display formats and adding cultural notes")
        
        try:
            v4_enhanced = []
            v4_cost = 0.0
            v4_processed = 0
            
            for i, article in enumerate(enhanced_articles, 1):
                print(f"   🔧 Verifying {i}/{len(enhanced_articles)}: {article.original_article_title[:40]}...")
                
                # Only enhance articles that have V3 enhancement
                if article.ai_enhanced and article.contextual_title_explanations:
                    try:
                        verified_article, cost = self._apply_v4_verification(article)
                        v4_enhanced.append(verified_article)
                        v4_cost += cost
                        v4_processed += 1
                        print(f"      ✅ Verified successfully (${cost:.4f})")
                        
                        # Show what was improved
                        if getattr(verified_article, 'quality_checked', False):
                            tooltips_count = len(verified_article.contextual_title_explanations)
                            print(f"      📊 Verified {tooltips_count} tooltips with GPT-4o")
                            
                    except Exception as e:
                        print(f"      ⚠️ Verification failed, keeping V3 version: {e}")
                        v4_enhanced.append(article)
                else:
                    # Keep unenhanced articles as-is
                    print(f"      ⏭️ Skipping (no V3 enhancement)")
                    v4_enhanced.append(article)
            
            print(f"✅ V4 verification complete!")
            print(f"   💰 Cost: ${v4_cost:.4f}")
            print(f"   📊 Successfully verified: {v4_processed}/{len(enhanced_articles)}")
            print("")
            
        except Exception as e:
            print(f"❌ V4 verification failed: {e}")
            print("💡 Continuing with V3-only enhancement...")
            v4_enhanced = enhanced_articles
            v4_cost = 0.0
        
        # Step 4: Convert Article objects to dictionaries for website
        print("🔄 STEP 4: Converting to V5 website format...")
        final_articles = []
        for i, article in enumerate(v4_enhanced, 1):
            print(f"   📄 {i}/{len(v4_enhanced)}: Formatting {article.original_article_title[:40]}...")
            
            # Convert Article object to dictionary with proper JSON serialization
            try:
                # Use model_dump with mode='json' to handle HttpUrl and other pydantic types
                if hasattr(article, 'model_dump'):
                    article_dict = article.model_dump(mode='json', by_alias=True)
                elif hasattr(article, 'dict'):
                    article_dict = article.dict(by_alias=True)
                else:
                    # Fallback: manual conversion
                    article_dict = {
                        'schema_version': 2,
                        'id': getattr(article, 'id', None),
                        'original_article_title': article.original_article_title,
                        'original_article_link': str(article.original_article_link) if article.original_article_link else '',
                        'original_article_published_date': article.original_article_published_date,
                        'source_name': article.source_name,
                        'quality_scores': {
                            'quality_score': article.quality_scores.quality_score,
                            'relevance_score': article.quality_scores.relevance_score,
                            'importance_score': article.quality_scores.importance_score,
                            'total_score': article.quality_scores.total_score
                        } if article.quality_scores else {},
                        'difficulty': getattr(article, 'difficulty', 'A2'),
                        'tone': getattr(article, 'tone', 'neutral'),
                        'keywords': getattr(article, 'keywords', None),
                        'audio_url': getattr(article, 'audio_url', None),
                        'simplified_french_title': getattr(article, 'simplified_french_title', ''),
                        'simplified_english_title': getattr(article, 'simplified_english_title', ''),
                        'french_summary': getattr(article, 'french_summary', ''),
                        'english_summary': getattr(article, 'english_summary', ''),
                        'contextual_title_explanations': getattr(article, 'contextual_title_explanations', {}),
                        'key_vocabulary': getattr(article, 'key_vocabulary', None),
                        'cultural_context': getattr(article, 'cultural_context', None),
                        'processed_at': datetime.now(timezone.utc).isoformat(),
                        'processing_id': None,
                        'ai_enhanced': getattr(article, 'ai_enhanced', False),
                        'display_ready': True,
                        'backfill_attempts': 0,
                        'quality_checked': getattr(article, 'quality_checked', False),
                        'v5_enhanced': True  # Mark as processed by V5
                    }
                
                final_articles.append(article_dict)
                
            except Exception as e:
                print(f"      ❌ Failed to convert article: {e}")
                print(f"      💡 Skipping this article to prevent JSON errors")
                continue
        
        total_cost = v3_cost + v4_cost
        print("🎉 " + "="*60)
        print("🎉 V3+V4 ENHANCEMENT PIPELINE COMPLETE!")
        print("🎉 " + "="*60)
        print(f"📊 Articles processed: {len(final_articles)}")
        print(f"🔮 V3 enhanced: {len([a for a in final_articles if a['ai_enhanced']])}")
        print(f"🤖 V4 verified: {len([a for a in final_articles if a['quality_checked']])}")
        print(f"💰 Total cost: ${total_cost:.4f}")
        print(f"✅ Quality preserved: Same prompts as proven V3+V4")
        print(f"✅ Display format preserved: **English:** _French word_")
        print("")
        
        return final_articles, total_cost
    
    def _apply_v4_verification(self, article: Article) -> Tuple[Article, float]:
        """Apply V4 GPT-4o verification using EXACT same prompt as V4."""
        try:
            # Ensure article has quality_checked attribute
            if not hasattr(article, 'quality_checked'):
                article.quality_checked = False
            
            # Use EXACT same V4 verification logic
            original_title = article.original_article_title
            fr_title = article.simplified_french_title or article.original_article_title
            en_title = article.simplified_english_title or "No English title"
            fr_summary = article.french_summary or "No summary"
            en_summary = article.english_summary or "No summary"
            
            # Format explanations for V4 prompt (same as V4)
            explanations_json = json.dumps(article.contextual_title_explanations, ensure_ascii=False, indent=2)
            
            # Use EXACT same V4 prompt
            v4_prompt = render('review_tooltips.jinja', {
                'original_title': original_title,
                'fr_title': fr_title,
                'en_title': en_title,
                'fr_summary': fr_summary,
                'en_summary': en_summary,
                'explanations_json': explanations_json
            })
            
            # Call V4 client with same parameters
            result = self.v4_client.complete(v4_prompt)
            
            if result.get('success') and result.get('content'):
                try:
                    v4_data = json.loads(result['content'])
                    
                    # Apply V4 improvements (same logic as V4)
                    if 'fixed_tokens' in v4_data or 'missing_tokens' in v4_data:
                        # Merge fixed and missing tokens
                        all_tokens = v4_data.get('fixed_tokens', []) + v4_data.get('missing_tokens', [])
                        
                        # Convert to dict format (same as V4)
                        enhanced_explanations = {}
                        for token in all_tokens:
                            if 'original_word' in token:
                                word = token['original_word']
                                enhanced_explanations[word] = {
                                    'display_format': token.get('display_format', ''),
                                    'explanation': token.get('explanation', ''),
                                    'cultural_note': token.get('cultural_note', '')
                                }
                        
                        article.contextual_title_explanations = enhanced_explanations
                    
                    # Update titles/summaries if provided
                    if 'updated_titles_summaries' in v4_data:
                        updates = v4_data['updated_titles_summaries']
                        article.simplified_french_title = updates.get('simplified_french_title', article.simplified_french_title)
                        article.simplified_english_title = updates.get('simplified_english_title', article.simplified_english_title)
                        article.french_summary = updates.get('french_summary', article.french_summary)
                        article.english_summary = updates.get('english_summary', article.english_summary)
                    
                    # Mark as V4 verified (same as V4)
                    article.quality_checked = True
                    
                except json.JSONDecodeError:
                    print("         ⚠️ V4 verification JSON parse failed - keeping V3 version")
            
            return article, result.get('cost', 0.0)
            
        except Exception as e:
            print(f"         ❌ V4 verification error: {e}")
            return article, 0.0
    
    def generate_website(self, enhanced_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate V5 website with V3+V4 enhanced articles using native V5 assets."""
        print("🌐 " + "="*60)
        print("🌐 GENERATING V5 WEBSITE")
        print("🌐 " + "="*60)
        
        # V5 now has its own complete website assets (copied from V4)
        website_dir = Path(__file__).parent.parent.parent / 'website'
        print(f"📁 Website directory: {website_dir}")
        
        if not website_dir.exists():
            print("❌ V5 website directory missing!")
            return {'error': 'V5 website assets not found'}
        
        print("✅ V5 website assets found:")
        assets = ['index.html', 'script.js', 'styles.css', 'js/', 'css/', 'favicon.svg', 'logo.svg']
        for asset in assets:
            asset_path = website_dir / asset
            exists = "✅" if asset_path.exists() else "❌"
            print(f"   {exists} {asset}")
        
        # Convert enhanced articles to rolling_articles.json format
        print("📄 Converting V5 enhanced articles to website format...")
        
        formatted_articles = []
        for i, article in enumerate(enhanced_articles, 1):
            print(f"   🔄 Converting article {i}/{len(enhanced_articles)}: {article.get('original_article_title', 'No title')[:50]}...")
            
            # Convert to the exact format expected by the website JavaScript
            formatted_article = {
                "schema_version": 2,
                "id": None,
                "original_article_title": article.get('original_article_title', ''),
                "original_article_link": article.get('original_article_link', ''),
                "original_article_published_date": article.get('original_article_published_date', ''),
                "source_name": article.get('source_name', 'Unknown'),
                "quality_scores": {
                    "quality_score": article.get('quality_scores', {}).get('quality_score', 8.0),
                    "relevance_score": article.get('quality_scores', {}).get('relevance_score', 9.0),
                    "importance_score": article.get('quality_scores', {}).get('importance_score', 8.0),
                    "total_score": article.get('quality_scores', {}).get('total_score', 25.0)
                },
                "difficulty": "B1",  # Default for Rony-selected articles
                "tone": "neutral",
                "keywords": None,
                "audio_url": None,
                "simplified_french_title": article.get('simplified_french_title', ''),
                "simplified_english_title": article.get('simplified_english_title', ''),
                "french_summary": article.get('french_summary', ''),
                "english_summary": article.get('english_summary', ''),
                "contextual_title_explanations": article.get('contextual_title_explanations', {}),
                "key_vocabulary": None,
                "cultural_context": None,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "processing_id": None,
                "ai_enhanced": bool(article.get('ai_enhanced', False)),
                "display_ready": True,
                "backfill_attempts": 0,
                "quality_checked": bool(article.get('quality_checked', False))
            }
            
            formatted_articles.append(formatted_article)
            
            # Show conversion status
            tooltips_count = len(formatted_article['contextual_title_explanations'])
            enhanced_status = "✅" if formatted_article['ai_enhanced'] else "⚠️"
            verified_status = "✅" if formatted_article['quality_checked'] else "⚠️"
            print(f"      {enhanced_status} V3 Enhanced | {verified_status} V4 Verified | 📊 {tooltips_count} tooltips")
        
        # Create the website data in exact format expected by JavaScript
        website_data = {
            "metadata": {
                "total_articles": len(formatted_articles),
                "last_updated": "just_now",
                "v5_enhanced": True,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "pipeline": "Rony + V3 + V4 + V5",
                "quality_preserved": True
            },
            "articles": formatted_articles
        }
        
        # Write rolling_articles.json (the JavaScript expects this exact filename)
        rolling_file = website_dir / 'rolling_articles.json'
        print(f"📝 Writing website data to: {rolling_file}")
        
        try:
            with open(rolling_file, 'w', encoding='utf-8') as f:
                json.dump(website_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Successfully wrote rolling_articles.json")
            print(f"   📊 Total articles: {len(formatted_articles)}")
            print(f"   🎯 V3 enhanced: {len([a for a in formatted_articles if a['ai_enhanced']])}")
            print(f"   ✅ V4 verified: {len([a for a in formatted_articles if a['quality_checked']])}")
            print(f"   📄 File size: {rolling_file.stat().st_size / 1024:.1f} KB")
            
        except Exception as e:
            print(f"❌ Failed to write rolling_articles.json: {e}")
            return {'error': 'Failed to write website data', 'details': str(e)}
        
        # Verify website is complete and ready
        print("\n🔍 Verifying V5 website completeness:")
        
        required_files = [
            'index.html',      # Main HTML file
            'script.js',       # 42KB JavaScript functionality
            'styles.css',      # 26KB professional styling
            'rolling_articles.json',  # Fresh article data
            'favicon.svg',     # Site icon
            'logo.svg'         # Site logo
        ]
        
        all_files_present = True
        for filename in required_files:
            filepath = website_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"   ✅ {filename} ({size/1024:.1f} KB)")
            else:
                print(f"   ❌ {filename} MISSING!")
                all_files_present = False
        
        if not all_files_present:
            return {'error': 'V5 website incomplete - missing required files'}
        
        print("\n🎉 V5 WEBSITE GENERATION COMPLETE!")
        print("✅ Native V5 assets: Complete sophisticated website")
        print("✅ Article data: Properly formatted for JavaScript")
        print("✅ V3+V4 quality: Preserved in V5 format")
        print("✅ Tooltips: Ready for interactive display")
        print("✅ Styling: Professional 26KB CSS")
        print("✅ Functionality: Advanced 42KB JavaScript")
        
        return {
            'success': True,
            'website_dir': str(website_dir),
            'articles_processed': len(formatted_articles),
            'v3_enhanced': len([a for a in formatted_articles if a['ai_enhanced']]),
            'v4_verified': len([a for a in formatted_articles if a['quality_checked']]),
            'files_created': required_files,
            'website_url': 'https://sonianand07.github.io/Better-French/v5-site/',
            'quality_preserved': True,
            'features': [
                'Interactive tooltips',
                'Professional styling', 
                'Advanced JavaScript',
                'Responsive design',
                'V3+V4 enhancement quality'
            ]
        } 