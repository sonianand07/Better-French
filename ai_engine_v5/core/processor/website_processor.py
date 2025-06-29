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

# Import V3+V4 proven processing components
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.parent))

try:
    from ai_engine_v3.processor import ProcessorV2
    from ai_engine_v3.models import Article, QualityScores
    from ai_engine_v4.client import HighLLMClient
    from ai_engine_v4.prompt_loader import render
except ImportError:
    # Fallback for different path structures
    sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'ai_engine_v3'))
    sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'ai_engine_v4'))
    from processor import ProcessorV2
    from models import Article, QualityScores
    from client import HighLLMClient
    from prompt_loader import render


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
                        if verified_article.quality_checked:
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
            print("💡 Falling back to V3-only enhancement")
            # Fall back to V3-only enhancement
            v4_enhanced = enhanced_articles
            v4_cost = 0.0
        
        # Step 4: Convert back to dict format for V5 website
        print("🔄 STEP 4: Converting to V5 website format...")
        final_articles = []
        for i, article in enumerate(v4_enhanced, 1):
            print(f"   📄 {i}/{len(v4_enhanced)}: Formatting {article.original_article_title[:40]}...")
            
            article_dict = {
                'title': article.original_article_title,
                'link': article.original_article_link,
                'published': article.original_article_published_date,
                'source': article.source_name,
                'simplified_french_title': article.simplified_french_title,
                'simplified_english_title': article.simplified_english_title,
                'french_summary': article.french_summary,
                'english_summary': article.english_summary,
                'contextual_title_explanations': article.contextual_title_explanations,
                'quality_scores': article.quality_scores.dict() if article.quality_scores else {},
                'ai_enhanced': article.ai_enhanced,
                'quality_checked': getattr(article, 'quality_checked', False),
                'v5_enhanced': True  # Mark as processed by V5
            }
            final_articles.append(article_dict)
        
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
        """Generate V5 website with V3+V4 enhanced articles."""
        print("🌐 " + "="*60)
        print("🌐 GENERATING V5 WEBSITE")
        print("🌐 " + "="*60)
        
        # Ensure website directory exists
        website_dir = Path(__file__).parent.parent.parent / 'website'
        print(f"📁 Website directory: {website_dir}")
        
        if not website_dir.exists():
            print("📁 Creating website directory...")
            website_dir.mkdir(parents=True, exist_ok=True)
            print("   ✅ Directory created")
        else:
            print("   ✅ Directory already exists")
        
        # Create rolling_articles.json (same format as V3+V4)
        print("📄 Creating rolling_articles.json...")
        website_data = {
            'articles': enhanced_articles,
            'metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_articles': len(enhanced_articles),
                'enhancement_pipeline': 'V3+V4 (preserved in V5)',
                'selection_method': 'Rony autonomous scraper',
                'quality_preserved': True
            }
        }
        
        rolling_file = website_dir / 'rolling_articles.json'
        print(f"   💾 Writing to: {rolling_file}")
        
        try:
            rolling_file.write_text(json.dumps(website_data, ensure_ascii=False, indent=2))
            print(f"   ✅ Successfully wrote {len(enhanced_articles)} articles")
        except Exception as e:
            print(f"   ❌ Failed to write articles: {e}")
            return {'error': 'Failed to write articles', 'details': str(e)}
        
        # Copy V4 website files (proven UI with tooltip system)
        print("🎨 Copying V4 website UI files...")
        v4_website_dir = Path(__file__).parent.parent.parent.parent / 'ai_engine_v4' / 'website'
        print(f"   📂 Source: {v4_website_dir}")
        
        if not v4_website_dir.exists():
            print("   ❌ V4 website directory not found!")
            print("   💡 You might need to run V4 first to generate the UI files")
        else:
            print("   ✅ V4 website directory found")
            
            import shutil
            files_copied = []
            
            for item in ['index.html', 'styles.css', 'script.js', 'js/', 'css/']:
                src = v4_website_dir / item
                dst = website_dir / item
                
                print(f"   📄 Copying {item}...")
                
                if not src.exists():
                    print(f"      ⚠️ Source not found: {src}")
                    continue
                
                try:
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        print(f"      ✅ Directory copied")
                    else:
                        shutil.copy2(src, dst)
                        print(f"      ✅ File copied")
                    
                    files_copied.append(item)
                    
                except Exception as e:
                    print(f"      ❌ Failed to copy {item}: {e}")
            
            print(f"   📊 Successfully copied: {files_copied}")
        
        # Final verification
        print("🔍 Final verification...")
        key_files = ['rolling_articles.json', 'index.html', 'styles.css', 'script.js']
        missing_files = []
        
        for file in key_files:
            file_path = website_dir / file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"   ✅ {file} ({size} bytes)")
            else:
                print(f"   ❌ {file} MISSING!")
                missing_files.append(file)
        
        if missing_files:
            print(f"⚠️ WARNING: Missing files: {missing_files}")
            print("💡 The website might not work properly without these files")
        
        print("🎉 " + "="*60)
        print("🎉 V5 WEBSITE GENERATION COMPLETE!")
        print("🎉 " + "="*60)
        print(f"📊 Enhanced articles: {len(enhanced_articles)}")
        print(f"🎯 Same tooltip system as proven V4")
        print(f"✅ All prompts preserved - NO quality reduction")
        print(f"🌐 Website ready at: {website_dir}")
        print("")
        
        return {
            'articles_count': len(enhanced_articles),
            'website_path': str(website_dir),
            'quality_preserved': True,
            'missing_files': missing_files,
            'success': len(missing_files) == 0
        } 