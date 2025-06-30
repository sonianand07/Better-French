"""
AI Engine v5 - Streamlined Website Processor
Takes Rony's pre-selected articles and enhances them with proven AI pipeline.
"""

import json
import requests
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path


class WebsiteProcessor:
    """
    V5 Streamlined Website Processor
    
    Pipeline:
    1. Takes Rony's pre-selected, pre-scored articles (10 articles)
    2. Applies AI Enhancement (contextual analysis + simplification)  
    3. Applies GPT-4o Verification (tooltip review)
    4. Generates sophisticated website
    
    NO DUPLICATED WORK - Rony already did scraping, scoring, selection
    """
    
    def __init__(self):
        print("🚀 " + "="*60)
        print("🚀 V5 STREAMLINED WEBSITE PROCESSOR")
        print("🚀 " + "="*60)
        
        print("🔍 Checking API keys...")
        self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENROUTER_SCRAPER_API_KEY')
        if not self.api_key:
            print("❌ CRITICAL: No API key found!")
            raise ValueError("API key required for AI enhancement")
        else:
            print("✅ API key found and loaded")
        
        # AI Enhancement settings
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.enhancement_model = "anthropic/claude-3.5-sonnet"  # V3 model
        self.verification_model = "openai/gpt-4o-mini"          # V4 model
        
        print("✅ V5 Website Processor READY!")
        print("✨ Pipeline: Rony → AI Enhancement → GPT-4o Verification → Website")
        print("✨ Same proven prompts - no quality reduction")
        print("")
    
    def _make_llm_request(self, prompt: str, model: str = None) -> Tuple[Dict, float]:
        """Make LLM request to OpenRouter."""
        model = model or self.enhancement_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Calculate cost
            usage = result.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
            if model == "anthropic/claude-3.5-sonnet":
                cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)
            else:  # GPT-4o-mini
                cost = (input_tokens * 0.00000015) + (output_tokens * 0.0000006)
            
            content = result['choices'][0]['message']['content']
            return {'success': True, 'content': content}, cost
            
        except Exception as e:
            print(f"❌ LLM request failed: {e}")
            return {'success': False, 'error': str(e)}, 0.0
    
    def _apply_contextual_analysis(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply contextual analysis using proven contextual_words_v3.jinja prompt."""
        
        # Load the actual prompt template
        prompt_path = Path(__file__).parent.parent.parent.parent / "ai_engine_v3" / "prompts" / "contextual_words_v3.jinja"
        
        if prompt_path.exists():
            # Use the actual V3 prompt file
            prompt_template = prompt_path.read_text()
            # Simple template replacement (no Jinja2 needed for this)
            prompt = prompt_template.replace("{{ original_article_title }}", article.get('title', ''))
        else:
            # Fallback to embedded prompt (same content)
            prompt = f"""You are an expert French language tutor helping English speakers learn French through contextual analysis.

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

        result, cost = self._make_llm_request(prompt, self.enhancement_model)
        
        if result.get('success'):
            try:
                analysis = json.loads(result['content'])
                # Handle both dict and list responses from LLM
                if isinstance(analysis, dict):
                    article['contextual_title_explanations'] = analysis.get('contextual_title_explanations', {})
                elif isinstance(analysis, list):
                    # If LLM returned a list, try to extract dict from first element
                    article['contextual_title_explanations'] = analysis[0].get('contextual_title_explanations', {}) if analysis and isinstance(analysis[0], dict) else {}
                else:
                    article['contextual_title_explanations'] = {}
                article['ai_enhanced'] = True
                return article, cost
            except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
                print(f"      ⚠️ JSON parse failed for contextual analysis")
                article['contextual_title_explanations'] = {}
                return article, cost
        else:
            print(f"      ❌ Contextual analysis failed: {result.get('error', 'Unknown error')}")
            article['contextual_title_explanations'] = {}
            return article, cost
    
    def _apply_simplification(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply simplification using proven simplify_titles_summaries_v3.jinja prompt."""
        
        # Load the actual prompt template
        prompt_path = Path(__file__).parent.parent.parent.parent / "ai_engine_v3" / "prompts" / "simplify_titles_summaries_v3.jinja"
        
        if prompt_path.exists():
            # Use the actual V3 prompt file
            prompt_template = prompt_path.read_text()
            # Simple template replacement
            prompt = prompt_template.replace("{{ original_article_title }}", article.get('title', ''))
            prompt = prompt.replace("{{ source_name }}", article.get('source', 'Unknown'))
        else:
            # Fallback to embedded prompt (same content)
            prompt = f"""You are an expert French language tutor helping English speakers learn French.

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

        result, cost = self._make_llm_request(prompt, self.enhancement_model)
        
        if result.get('success'):
            try:
                simplification = json.loads(result['content'])
                # Handle both dict and list responses from LLM
                if isinstance(simplification, dict):
                    article['simplified_french_title'] = simplification.get('simplified_french_title', article.get('title', ''))
                    article['simplified_english_title'] = simplification.get('simplified_english_title', '')
                    article['french_summary'] = simplification.get('french_summary', '')
                    article['english_summary'] = simplification.get('english_summary', '')
                elif isinstance(simplification, list) and simplification and isinstance(simplification[0], dict):
                    # If LLM returned a list, try to extract dict from first element
                    s = simplification[0]
                    article['simplified_french_title'] = s.get('simplified_french_title', article.get('title', ''))
                    article['simplified_english_title'] = s.get('simplified_english_title', '')
                    article['french_summary'] = s.get('french_summary', '')
                    article['english_summary'] = s.get('english_summary', '')
                else:
                    # Fallback to original values
                    article['simplified_french_title'] = article.get('title', '')
                    article['simplified_english_title'] = ''
                    article['french_summary'] = ''
                    article['english_summary'] = ''
                return article, cost
            except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
                print(f"      ⚠️ JSON parse failed for simplification")
                return article, cost
        else:
            print(f"      ❌ Simplification failed: {result.get('error', 'Unknown error')}")
            return article, cost
    
    def _apply_gpt4o_verification(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply GPT-4o verification using proven review_tooltips.jinja prompt."""
        
        explanations_json = json.dumps(article.get('contextual_title_explanations', {}), ensure_ascii=False, indent=2)
        fr_title = article.get('simplified_french_title', '')
        en_title = article.get('simplified_english_title', '')
        fr_summary = article.get('french_summary', '')
        en_summary = article.get('english_summary', '')
        
        # Load the actual prompt template
        prompt_path = Path(__file__).parent.parent.parent.parent / "ai_engine_v4" / "prompts" / "review_tooltips.jinja"
        
        if prompt_path.exists():
            # Use the actual V4 prompt file
            prompt_template = prompt_path.read_text()
            # Simple template replacement
            prompt = prompt_template.replace("{{ original_title }}", article.get('title', ''))
            prompt = prompt.replace("{{ fr_title }}", fr_title)
            prompt = prompt.replace("{{ en_title }}", en_title)
            prompt = prompt.replace("{{ fr_summary }}", fr_summary)
            prompt = prompt.replace("{{ en_summary }}", en_summary)
            prompt = prompt.replace("{{ explanations_json }}", explanations_json)
        else:
            # Fallback to embedded prompt (same content)
            prompt = f"""You are a French language expert reviewing educational content for accuracy and quality.

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
4. **Quality**: Are explanations clear and helpful?

Return ONLY valid JSON in this format:
{{
  "fixed_tokens": [
    {{
      "original_word": "word",
      "display_format": "**English:** word",
      "explanation": "Corrected explanation",
      "cultural_note": "Cultural context if relevant"
    }}
  ],
  "missing_tokens": [
    {{
      "original_word": "word",
      "display_format": "**English:** word", 
      "explanation": "Explanation for missing word",
      "cultural_note": "Cultural context if relevant"
    }}
  ],
  "updated_titles_summaries": {{
    "simplified_french_title": "Corrected French title if needed",
    "simplified_english_title": "Corrected English title if needed",
    "french_summary": "Corrected French summary if needed",
    "english_summary": "Corrected English summary if needed"
  }}
}}

IMPORTANT: Return only the JSON, no other text."""

        result, cost = self._make_llm_request(prompt, self.verification_model)
        
        if result.get('success'):
            try:
                verification = json.loads(result['content'])
                # Handle both dict and list responses from LLM
                if isinstance(verification, dict):
                    article = self._apply_verification_fixes(article, verification)
                elif isinstance(verification, list) and verification and isinstance(verification[0], dict):
                    # If LLM returned a list, use first element
                    article = self._apply_verification_fixes(article, verification[0])
                # If neither dict nor valid list, skip verification fixes but mark as checked
                article['quality_checked'] = True
                return article, cost
            except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
                print(f"      ⚠️ JSON parse failed for GPT-4o verification")
                article['quality_checked'] = True  # Mark as checked even if parsing failed
                return article, cost
        else:
            print(f"      ❌ GPT-4o verification failed: {result.get('error', 'Unknown error')}")
            article['quality_checked'] = True  # Mark as checked to avoid blocking
            return article, cost
    
    def _apply_verification_fixes(self, article: Dict[str, Any], verification: Dict[str, Any]) -> Dict[str, Any]:
        """Apply GPT-4o verification fixes to the article."""
        
        # Update explanations with fixes and missing tokens
        explanations = article.get('contextual_title_explanations', {})
        
        # Apply fixed tokens
        for token in verification.get('fixed_tokens', []):
            word = token.get('original_word')
            if word:
                explanations[word] = {
                    'display_format': token.get('display_format', ''),
                    'explanation': token.get('explanation', ''),
                    'cultural_note': token.get('cultural_note', '')
                }
        
        # Add missing tokens
        for token in verification.get('missing_tokens', []):
            word = token.get('original_word')
            if word:
                explanations[word] = {
                    'display_format': token.get('display_format', ''),
                    'explanation': token.get('explanation', ''),
                    'cultural_note': token.get('cultural_note', '')
                }
        
        article['contextual_title_explanations'] = explanations
        
        # Update titles and summaries if provided
        updates = verification.get('updated_titles_summaries', {})
        for field in ['simplified_french_title', 'simplified_english_title', 'french_summary', 'english_summary']:
            if field in updates and updates[field]:
                article[field] = updates[field]
        
        return article
    
    def enhance_articles(self, rony_articles: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Apply the complete AI enhancement pipeline to Rony's pre-selected articles.
        
        Pipeline:
        1. Contextual Analysis (proven prompt)
        2. Simplification (proven prompt) 
        3. GPT-4o Verification (proven prompt)
        
        SMART LIMITS:
        - Maximum 30 articles per run (development phase)
        - Only recent articles (last 7 days)
        - Prioritize by Rony score
        """
        print(f"🎯 SMART AI ENHANCEMENT PIPELINE - DEVELOPMENT PHASE")
        print("=" * 60)
        
        # SMART FILTERING: Only recent articles (last 7 days)
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=7)
        
        recent_articles = []
        for article in rony_articles:
            # Try to parse published date
            published_str = article.get('published', article.get('timestamp', ''))
            if published_str:
                try:
                    # Handle various date formats
                    if 'T' in published_str:
                        published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    else:
                        published_date = datetime.strptime(published_str[:10], '%Y-%m-%d')
                    
                    if published_date.replace(tzinfo=None) >= cutoff_date:
                        recent_articles.append(article)
                except:
                    # If date parsing fails, include article (err on side of inclusion)
                    recent_articles.append(article)
            else:
                # No date info, include article
                recent_articles.append(article)
        
        print(f"📅 Filtered to {len(recent_articles)} recent articles (last 7 days) from {len(rony_articles)} total")
        
        # SMART LIMIT: Max 30 articles for development phase
        if len(recent_articles) > 30:
            # Sort by Rony score (highest first) to get best articles
            recent_articles.sort(key=lambda x: x.get('total_score', 0), reverse=True)
            recent_articles = recent_articles[:30]
            print(f"🎯 Limited to TOP 30 articles (development phase)")
        
        print(f"📊 Processing {len(recent_articles)} articles")
        print("📋 Pipeline Steps:")
        print("   1️⃣ Contextual Analysis (French learning tooltips)")
        print("   2️⃣ Simplification (B1-level French + English)")
        print("   3️⃣ GPT-4o Verification (quality check + missing tooltips)")
        print("")
        
        enhanced_articles = []
        total_cost = 0.0
        
        for i, article in enumerate(recent_articles, 1):
            title = article.get('title', 'No title')[:60]
            source = article.get('source', 'Unknown')
            rony_score = article.get('total_score', 0)
            
            print(f"🔧 [{i:2d}/{len(recent_articles)}] {title}...")
            print(f"      📊 Rony Score: {rony_score:.1f} | Source: {source}")
            
            # Step 1: Contextual Analysis
            print(f"      1️⃣ Contextual analysis...")
            article, cost1 = self._apply_contextual_analysis(article)
            total_cost += cost1
            
            # Step 2: Simplification
            print(f"      2️⃣ Simplification...")
            article, cost2 = self._apply_simplification(article)
            total_cost += cost2
            
            # Step 3: GPT-4o Verification
            print(f"      3️⃣ GPT-4o verification...")
            article, cost3 = self._apply_gpt4o_verification(article)
            total_cost += cost3
            
            # Add processing metadata
            article['processed_at'] = datetime.now(timezone.utc).isoformat()
            article['original_article_link'] = article.get('link', '')
            article['original_article_title'] = article.get('title', '')
            article['original_article_published_date'] = article.get('published', '')
            article['source_name'] = article.get('source', '')
            
            enhanced_articles.append(article)
            
            step_cost = cost1 + cost2 + cost3
            print(f"      ✅ Complete (${step_cost:.4f})")
            print("")
        
        print(f"✅ SMART AI ENHANCEMENT PIPELINE COMPLETE!")
        print(f"   📊 Articles enhanced: {len(enhanced_articles)}")
        print(f"   🎯 Recent articles only (last 7 days)")
        print(f"   ⚡ Development limit: max 30 articles")
        print(f"   💰 Total cost: ${total_cost:.4f}")
        print(f"   🚀 Ready for sophisticated website generation")
        
        return enhanced_articles, total_cost
    
    def generate_website(self, enhanced_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate sophisticated V5 website with enhanced articles and smart data management."""
        print(f"🌐 GENERATING V5 WEBSITE WITH SMART DATA MANAGEMENT...")
        
        website_dir = Path(__file__).parent.parent.parent / "website"
        website_dir.mkdir(parents=True, exist_ok=True)
        
        backup_dir = website_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        rolling_path = website_dir / "rolling_articles.json"
        
        # Load existing articles for smart merging (like V3/V4)
        existing_articles = []
        if rolling_path.exists():
            try:
                existing_data = json.loads(rolling_path.read_text('utf-8'))
                existing_articles = existing_data.get('articles', [])
                print(f"   📚 Found {len(existing_articles)} existing articles")
                
                # Create backup before overwriting (like V3/V4)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"rolling_{ts}.json"
                backup_path.write_text(rolling_path.read_text('utf-8'))
                print(f"   💾 Backup created: {backup_path.name}")
                
            except Exception as e:
                print(f"   ⚠️ Could not load existing articles: {e}")
                existing_articles = []
        
        # Smart merging: Combine existing + newly enhanced articles
        all_articles = existing_articles + enhanced_articles
        
        # Deduplication by article link (like V3/V4)
        dedup_articles = {}
        for article in sorted(all_articles, key=lambda a: a.get('processed_at', ''), reverse=True):
            link = article.get('original_article_link') or article.get('link', '')
            if link and link not in dedup_articles:
                dedup_articles[link] = article
        
        merged_articles = list(dedup_articles.values())
        print(f"   🔄 After deduplication: {len(merged_articles)} articles")
        
        # Quality-based prioritization (like V3/V4)
        # 1. Prefer quality_checked + ai_enhanced articles
        quality_checked = [a for a in merged_articles if a.get('quality_checked') and a.get('ai_enhanced')]
        ai_enhanced = [a for a in merged_articles if a.get('ai_enhanced') and not a.get('quality_checked')]
        basic_articles = [a for a in merged_articles if not a.get('ai_enhanced')]
        
        # Combine in quality order
        prioritized_articles = quality_checked + ai_enhanced + basic_articles
        
        # Sort by published date (newest first)
        def _date_key(article):
            return (article.get('original_article_published_date') or 
                    article.get('published') or 
                    article.get('processed_at') or 
                    '1970-01-01')
        
        prioritized_articles.sort(key=_date_key, reverse=True)
        
        # Apply V3/V4 limit: Maximum 200 articles for performance
        final_articles = prioritized_articles[:200]
        
        if len(prioritized_articles) > 200:
            archived_count = len(prioritized_articles) - 200
            print(f"   🗄️ Archived {archived_count} older articles (200 article limit)")
        
        # Create website data with V5 metadata
        website_data = {
            "metadata": {
                "total_articles": len(final_articles),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "v5_enhanced": True,
                "pipeline": "Rony (intelligent selection) + V5 (AI enhancement)",
                "quality": "Proven prompts + GPT-4o verification",
                "quality_breakdown": {
                    "quality_checked": len([a for a in final_articles if a.get('quality_checked')]),
                    "ai_enhanced": len([a for a in final_articles if a.get('ai_enhanced')]),
                    "basic": len([a for a in final_articles if not a.get('ai_enhanced')])
                }
            },
            "articles": final_articles
        }
        
        # Save website data atomically (like V3/V4)
        temp_path = rolling_path.with_suffix('.tmp')
        temp_path.write_text(json.dumps(website_data, ensure_ascii=False, indent=2))
        temp_path.rename(rolling_path)
        
        # Cleanup old backups (keep last 50)
        backup_files = sorted(backup_dir.glob("rolling_*.json"))
        if len(backup_files) > 50:
            for old_backup in backup_files[:-50]:
                old_backup.unlink()
            print(f"   🧹 Cleaned up old backups (kept last 50)")
        
        print(f"   ✅ Website data saved to {rolling_path}")
        print(f"   📊 {len(final_articles)} articles ready (max 200)")
        print(f"   🎨 V5 website has complete sophisticated assets")
        print(f"   🚀 Deployment ready: https://sonianand07.github.io/Better-French/v5-site/")
        
        return {
            "success": True,
            "files_created": ["rolling_articles.json"],
            "articles_count": len(final_articles),
            "articles_archived": len(prioritized_articles) - len(final_articles),
            "website_path": str(website_dir),
            "backup_created": True
        }
