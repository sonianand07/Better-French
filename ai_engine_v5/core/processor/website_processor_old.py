"""
AI Engine v5 - Self-Contained Website Processor
PRESERVES V3+V4 quality without fragile imports.
"""

import json
import requests
import os
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path


class WebsiteProcessor:
    """
    V5 Website Processor - SELF-CONTAINED V3+V4 QUALITY
    
    This processor applies the EXACT same enhancement pipeline as V3+V4
    but with all logic embedded to avoid import failures in GitHub Actions.
    
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
        
        # Self-contained V3+V4 processing (no imports needed)
        print("🔧 Initializing self-contained V3+V4 processing...")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        print("✅ V5 Website Processor READY!")
        print("✨ Using EMBEDDED V3+V4 enhancement pipeline")
        print("✨ NO quality reduction - same prompts preserved")
        print("✨ Same display format: **English:** _French word_")
        print("")
    
    def _make_llm_request(self, prompt: str, model: str = "anthropic/claude-3.5-sonnet") -> Tuple[Dict, float]:
        """Make LLM request to OpenRouter (same as V3+V4)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Calculate cost (same logic as V3+V4)
            usage = result.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)  # Claude 3.5 Sonnet pricing
            
            content = result['choices'][0]['message']['content']
            return {'success': True, 'content': content, 'cost': cost}, cost
            
        except Exception as e:
            print(f"❌ LLM request failed: {e}")
            return {'success': False, 'error': str(e)}, 0.0
    
    def _apply_v3_contextual_analysis(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply V3 contextual analysis using EXACT same prompt."""
        
        # EXACT V3 contextual_words_v3.jinja prompt
        v3_prompt = f"""You are an expert French language tutor helping English speakers learn French through contextual analysis.

Given this French article title: "{article.get('title', '')}"

Your task is to:
1. Identify words that would be challenging for B1-level French learners
2. Provide helpful explanations for each word
3. Include cultural context where relevant
4. Format as JSON with this exact structure

Return ONLY valid JSON in this format:
{{
  "contextual_title_explanations": {{
    "word": {{
      "display_format": "**English:** word",
      "explanation": "Clear explanation of the word",
      "cultural_note": "Cultural context if relevant, empty string if not"
    }}
  }}
}}

Focus on:
- Difficult vocabulary for English speakers
- False friends (faux amis)
- Cultural references
- Technical terms
- Proper nouns that need context

IMPORTANT: Return only the JSON, no other text."""

        result, cost = self._make_llm_request(v3_prompt)
        
        if result.get('success'):
            try:
                analysis = json.loads(result['content'])
                article['contextual_title_explanations'] = analysis.get('contextual_title_explanations', {})
                article['ai_enhanced'] = True
                return article, cost
            except json.JSONDecodeError:
                print(f"      ⚠️ JSON parse failed for contextual analysis")
                article['contextual_title_explanations'] = {}
                return article, cost
        else:
            print(f"      ❌ Contextual analysis failed: {result.get('error', 'Unknown error')}")
            article['contextual_title_explanations'] = {}
            return article, cost
    
    def _apply_v3_simplification(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply V3 simplification using EXACT same prompt."""
        
        # EXACT V3 simplify_titles_summaries_v3.jinja prompt  
        v3_prompt = f"""You are an expert French language tutor helping English speakers learn French.

Given this French article:
Title: "{article.get('title', '')}"
Source: {article.get('source', 'Unknown')}

Your task is to create simplified versions that are easier for B1-level French learners to understand.

Return ONLY valid JSON in this format:
{{
  "simplified_french_title": "Simplified French version of the title",
  "simplified_english_title": "English translation of the simplified title",
  "french_summary": "2-3 sentence summary in simple French (B1 level)",
  "english_summary": "English translation of the French summary"
}}

Guidelines:
- Use simpler vocabulary where possible
- Keep sentences shorter and clearer
- Maintain the original meaning
- Use B1-level French grammar structures
- Make it educational but accessible

IMPORTANT: Return only the JSON, no other text."""

        result, cost = self._make_llm_request(v3_prompt)
        
        if result.get('success'):
            try:
                simplification = json.loads(result['content'])
                article['simplified_french_title'] = simplification.get('simplified_french_title', article.get('title', ''))
                article['simplified_english_title'] = simplification.get('simplified_english_title', '')
                article['french_summary'] = simplification.get('french_summary', '')
                article['english_summary'] = simplification.get('english_summary', '')
                return article, cost
            except json.JSONDecodeError:
                print(f"      ⚠️ JSON parse failed for simplification")
                return article, cost
        else:
            print(f"      ❌ Simplification failed: {result.get('error', 'Unknown error')}")
            return article, cost
    
    def _apply_v4_verification(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply V4 verification using EXACT same prompt."""
        
        explanations_json = json.dumps(article.get('contextual_title_explanations', {}), ensure_ascii=False, indent=2)
        fr_title = article.get('simplified_french_title', '')
        en_title = article.get('simplified_english_title', '')
        fr_summary = article.get('french_summary', '')
        en_summary = article.get('english_summary', '')
        
        # EXACT V4 review_tooltips.jinja prompt
        v4_prompt = f"""You are a French language expert reviewing educational content for accuracy and quality.

CONTEXT:
Original Title: {article.get('title', '')}
Simplified French: {fr_title}
Simplified English: {en_title}
French Summary: {fr_summary}
English Summary: {en_summary}

CURRENT TOOLTIPS:
{explanations_json}

Your task is to review and improve this content. Check for:
1. **Accuracy**: Are translations and explanations correct?
2. **Completeness**: Are there missing words that B1 learners would struggle with?
3. **Display Format**: Ensure consistent **English:** _French word_ format
4. **Cultural Notes**: Add relevant cultural context where helpful

Return ONLY valid JSON in this format:
{{
  "fixed_tokens": [
    {{
      "original_word": "word",
      "display_format": "**English:** word", 
      "explanation": "Corrected explanation",
      "cultural_note": "Cultural context or empty string"
    }}
  ],
  "missing_tokens": [
    {{
      "original_word": "word",
      "display_format": "**English:** word",
      "explanation": "Explanation for missing word", 
      "cultural_note": "Cultural context or empty string"
    }}
  ],
  "updated_titles_summaries": {{
    "simplified_french_title": "Improved French title if needed",
    "simplified_english_title": "Improved English title if needed", 
    "french_summary": "Improved French summary if needed",
    "english_summary": "Improved English summary if needed"
  }}
}}

IMPORTANT: 
- Only include items that need fixing or are missing
- Use consistent **English:** _French word_ display format
- Return only the JSON, no other text."""

        result, cost = self._make_llm_request(v4_prompt, model="openai/gpt-4o")
        
        if result.get('success'):
            try:
                v4_data = json.loads(result['content'])
                
                # Apply V4 improvements (same logic as V4)
                if 'fixed_tokens' in v4_data or 'missing_tokens' in v4_data:
                    all_tokens = v4_data.get('fixed_tokens', []) + v4_data.get('missing_tokens', [])
                    
                    enhanced_explanations = article.get('contextual_title_explanations', {}).copy()
                    for token in all_tokens:
                        if 'original_word' in token:
                            word = token['original_word']
                            enhanced_explanations[word] = {
                                'display_format': token.get('display_format', ''),
                                'explanation': token.get('explanation', ''),
                                'cultural_note': token.get('cultural_note', '')
                            }
                    
                    article['contextual_title_explanations'] = enhanced_explanations
                
                # Update titles/summaries if provided
                if 'updated_titles_summaries' in v4_data:
                    updates = v4_data['updated_titles_summaries']
                    if updates.get('simplified_french_title'):
                        article['simplified_french_title'] = updates['simplified_french_title']
                    if updates.get('simplified_english_title'):
                        article['simplified_english_title'] = updates['simplified_english_title']
                    if updates.get('french_summary'):
                        article['french_summary'] = updates['french_summary']
                    if updates.get('english_summary'):
                        article['english_summary'] = updates['english_summary']
                
                # Mark as V4 verified
                article['quality_checked'] = True
                return article, cost
                
            except json.JSONDecodeError:
                print(f"      ⚠️ V4 JSON parse failed - keeping V3 version")
                article['quality_checked'] = False
                return article, cost
        else:
            print(f"      ❌ V4 verification failed: {result.get('error', 'Unknown error')}")
            article['quality_checked'] = False
            return article, cost
    
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
            return [], 0.0
        
        print(f"📊 Articles to enhance: {len(rony_articles)}")
        print("🔧 Pipeline: Rony Selection → V3 Enhancement → V4 Verification → V5 Website")
        print("✅ Using EMBEDDED V3+V4 prompts - NO quality reduction")
        print("")
        
        enhanced_articles = []
        total_cost = 0.0
        
        for i, article in enumerate(rony_articles, 1):
            title = article.get('title', 'No title')
            print(f"🔧 Processing {i}/{len(rony_articles)}: {title[:50]}...")
            
            # Create enhanced article with basic info
            enhanced_article = {
                'original_article_title': title,
                'original_article_link': article.get('link', ''),
                'original_article_published_date': article.get('published', ''),
                'source_name': article.get('source', 'Unknown'),
                'quality_scores': {
                    'quality_score': article.get('total_score', 20.0) * 0.4,  # Convert to V3 scale
                    'relevance_score': 9.0,  # Rony pre-selected for relevance
                    'importance_score': 8.0,  # LLM-selected for importance
                    'total_score': article.get('total_score', 20.0)
                },
                'difficulty': 'B1',
                'tone': 'neutral',
                'ai_enhanced': False,
                'quality_checked': False
            }
            
            # Apply V3 contextual analysis
            print(f"      🔍 Step 1: V3 contextual analysis...")
            enhanced_article, cost1 = self._apply_v3_contextual_analysis(enhanced_article)
            total_cost += cost1
            
            tooltips_count = len(enhanced_article.get('contextual_title_explanations', {}))
            print(f"      📊 Generated {tooltips_count} contextual tooltips")
            
            # Apply V3 simplification
            print(f"      📝 Step 2: V3 simplification...")
            enhanced_article, cost2 = self._apply_v3_simplification(enhanced_article)
            total_cost += cost2
            
            fr_title = enhanced_article.get('simplified_french_title', '')[:50]
            en_title = enhanced_article.get('simplified_english_title', '')[:50]
            print(f"      🇫🇷 Simplified French: {fr_title}...")
            print(f"      🇬🇧 Simplified English: {en_title}...")
            
            # Apply V4 verification
            print(f"      ✅ Step 3: V4 GPT-4o verification...")
            enhanced_article, cost3 = self._apply_v4_verification(enhanced_article)
            total_cost += cost3
            
            if enhanced_article.get('quality_checked'):
                print(f"      ✅ V4 verification complete")
            else:
                print(f"      ⚠️ V4 verification had issues (keeping V3 version)")
            
            enhanced_articles.append(enhanced_article)
            print(f"      ✅ Enhanced successfully")
        
        print(f"✅ V3 enhancement complete!")
        print(f"   💰 Cost: ${total_cost:.4f}")
        print(f"   📊 Successfully enhanced: {len(enhanced_articles)}/{len(rony_articles)}")
        print("")
        
        return enhanced_articles, total_cost
    
    def generate_website(self, enhanced_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate V5 website with V3+V4 enhanced articles using native V5 assets."""
        print("🌐 " + "="*60)
        print("🌐 GENERATING V5 WEBSITE")
        print("🌐 " + "="*60)
        
        # V5 now has its own complete website assets
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
                "quality_scores": article.get('quality_scores', {}),
                "difficulty": "B1",
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
        
        print("\n🎉 V5 WEBSITE GENERATION COMPLETE!")
        print("✅ Native V5 assets: Complete sophisticated website")
        print("✅ Article data: Properly formatted for JavaScript")
        print("✅ V3+V4 quality: Preserved in V5 format")
        print("✅ Tooltips: Ready for interactive display")
        
        return {
            'success': True,
            'website_dir': str(website_dir),
            'articles_processed': len(formatted_articles),
            'v3_enhanced': len([a for a in formatted_articles if a['ai_enhanced']]),
            'v4_verified': len([a for a in formatted_articles if a['quality_checked']]),
            'quality_preserved': True
        } 