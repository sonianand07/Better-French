"""
AI Engine v5 - Website Processor
Applies V3 + V4 enhancement pipeline to scraped articles.
"""

import json
import requests
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path


class WebsiteProcessor:
    """Self-contained website processor that applies V3+V4 enhancement."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.v3_model = os.getenv('AI_ENGINE_V3_MODEL', 'google/gemini-2.0-flash-exp')
        self.v4_model = os.getenv('AI_ENGINE_V4_MODEL', 'openai/gpt-4o-mini')
        
    def enhance_articles(self, articles: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        """Apply V3 + V4 enhancement pipeline to articles."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")
        
        enhanced_articles = []
        total_cost = 0.0
        
        print(f"🔧 Enhancing {len(articles)} articles with V3+V4 pipeline...")
        
        for i, article in enumerate(articles, 1):
            try:
                print(f"  📄 Processing article {i}/{len(articles)}: {article['title'][:50]}...")
                
                # Step 1: V3 Enhancement (Contextual words + Simplification)
                v3_enhanced, v3_cost = self._apply_v3_enhancement(article)
                total_cost += v3_cost
                
                # Step 2: V4 Enhancement (GPT-4o verification + tooltip quality)
                v4_enhanced, v4_cost = self._apply_v4_enhancement(v3_enhanced)
                total_cost += v4_cost
                
                enhanced_articles.append(v4_enhanced)
                print(f"    ✅ Enhanced (V3: ${v3_cost:.3f}, V4: ${v4_cost:.3f})")
                
            except Exception as e:
                print(f"    ⚠️ Enhancement failed for article {i}: {e}")
                # Add article without enhancement as fallback
                enhanced_articles.append(article)
                continue
        
        print(f"🎉 Enhancement complete: {len(enhanced_articles)} articles processed")
        return enhanced_articles, total_cost
    
    def _apply_v3_enhancement(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply V3 enhancement: contextual words + simplification."""
        
        # V3 Enhancement prompt
        v3_prompt = f"""Transform this French news article for language learners:

ORIGINAL ARTICLE:
Title: {article['title']}
Summary: {article.get('summary', 'No summary available')}
Source: {article.get('source', 'Unknown')}

TASKS:
1. SIMPLIFY the title to B1-B2 French level
2. SIMPLIFY the summary to B1-B2 French level
3. IDENTIFY 5-8 key vocabulary words for learning
4. For each word, provide: definition, example sentence, difficulty level

Respond with EXACTLY this JSON format:
{{
    "simplified_title": "Simplified French title",
    "simplified_summary": "Simplified French summary (2-3 sentences)",
    "vocabulary_words": [
        {{
            "word": "mot",
            "definition": "French definition",
            "example": "Example sentence in French",
            "difficulty": "B1/B2/C1",
            "translation": "English translation"
        }}
    ]
}}"""
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.v3_model,
                    "messages": [{"role": "user", "content": v3_prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Calculate cost
            usage = result.get('usage', {})
            cost = self._calculate_cost(usage, 'v3')
            
            # Parse response
            llm_content = result['choices'][0]['message']['content'].strip()
            
            try:
                v3_data = json.loads(llm_content)
                
                # Create V3 enhanced article
                enhanced = {
                    **article,
                    'french_title': v3_data['simplified_title'],
                    'french_summary': v3_data['simplified_summary'],
                    'vocabulary_words': v3_data['vocabulary_words'],
                    'original_article_title': article['title'],
                    'original_article_link': article['link'],
                    'original_article_published_date': article.get('published_date', ''),
                    'source_name': article.get('source', 'Unknown'),
                    'v3_enhanced': True
                }
                
                return enhanced, cost
                
            except json.JSONDecodeError:
                # Fallback on JSON parsing error
                return article, cost
                
        except Exception as e:
            print(f"V3 enhancement failed: {e}")
            return article, 0.0
    
    def _apply_v4_enhancement(self, article: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Apply V4 enhancement: GPT-4o verification + tooltip quality."""
        
        vocabulary_words = article.get('vocabulary_words', [])
        if not vocabulary_words:
            return article, 0.0
        
        # V4 Enhancement prompt
        vocab_text = "\n".join([
            f"- {word['word']}: {word['definition']} (Example: {word['example']})"
            for word in vocabulary_words
        ])
        
        v4_prompt = f"""Review and enhance these French vocabulary explanations for language learners:

ARTICLE: {article.get('french_title', article['title'])}
VOCABULARY TO REVIEW:
{vocab_text}

IMPROVEMENTS NEEDED:
1. Verify definitions are accurate and learner-friendly
2. Ensure examples are natural and contextual
3. Add pronunciation hints where helpful
4. Check difficulty levels are appropriate
5. Enhance with learning tips if beneficial

Respond with EXACTLY this JSON format:
{{
    "reviewed_vocabulary": [
        {{
            "word": "mot",
            "definition": "Improved French definition",
            "example": "Better example sentence",
            "difficulty": "B1/B2/C1",
            "translation": "English translation",
            "learning_tip": "Optional helpful tip"
        }}
    ],
    "review_notes": "Brief notes about improvements made"
}}"""
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.v4_model,
                    "messages": [{"role": "user", "content": v4_prompt}],
                    "temperature": 0.2,
                    "max_tokens": 1200
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Calculate cost
            usage = result.get('usage', {})
            cost = self._calculate_cost(usage, 'v4')
            
            # Parse response
            llm_content = result['choices'][0]['message']['content'].strip()
            
            try:
                v4_data = json.loads(llm_content)
                
                # Create V4 enhanced article
                enhanced = {
                    **article,
                    'vocabulary_words': v4_data['reviewed_vocabulary'],
                    'v4_enhanced': True,
                    'v4_review_notes': v4_data.get('review_notes', '')
                }
                
                return enhanced, cost
                
            except json.JSONDecodeError:
                # Fallback: return V3 version
                return article, cost
                
        except Exception as e:
            print(f"V4 enhancement failed: {e}")
            return article, 0.0
    
    def _calculate_cost(self, usage: Dict[str, Any], version: str) -> float:
        """Calculate API cost based on usage."""
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        # Rough pricing estimates
        if version == 'v3':  # Gemini 2.0 Flash
            return (prompt_tokens * 0.00001) + (completion_tokens * 0.00003)
        else:  # V4 - GPT-4o mini
            return (prompt_tokens * 0.00015) + (completion_tokens * 0.0006)
    
    def generate_website(self, enhanced_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate the website with enhanced articles."""
        
        print("🌐 Generating V5 website...")
        
        # Create website directory
        website_dir = Path('ai_engine_v5/website')
        website_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate main data file
        website_data = {
            "articles": enhanced_articles,
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_articles": len(enhanced_articles),
                "v5_features": [
                    "Autonomous hourly scraping",
                    "LLM-powered article selection", 
                    "V3 + V4 enhancement pipeline",
                    "Separated workflow architecture"
                ]
            }
        }
        
        # Save articles data
        articles_file = website_dir / 'rolling_articles.json'
        articles_file.write_text(json.dumps(website_data, indent=2, ensure_ascii=False))
        
        # Generate website HTML
        self._generate_website_html(website_dir, enhanced_articles)
        
        print(f"✅ Website generated with {len(enhanced_articles)} articles")
        
        return {
            "articles_count": len(enhanced_articles),
            "website_path": str(website_dir),
            "data_file": str(articles_file)
        }
    
    def _generate_website_html(self, website_dir: Path, articles: List[Dict[str, Any]]):
        """Generate the HTML website."""
        
        # Generate article HTML
        articles_html = []
        for i, article in enumerate(articles, 1):
            vocab_html = ""
            for word_data in article.get('vocabulary_words', []):
                word = word_data.get('word', '')
                definition = word_data.get('definition', '')
                example = word_data.get('example', '')
                vocab_html += f"""
                <div class="vocabulary-item">
                    <strong>{word}</strong>: {definition}<br>
                    <em>Exemple: {example}</em>
                </div>"""
            
            article_html = f"""
            <div class="article-card">
                <h2>{article.get('french_title', article['title'])}</h2>
                <p class="summary">{article.get('french_summary', article.get('summary', ''))}</p>
                <div class="vocabulary-section">
                    <h3>📚 Vocabulaire</h3>
                    {vocab_html}
                </div>
                <div class="article-meta">
                    <span>Source: {article.get('source_name', 'Unknown')}</span>
                    <a href="{article['link']}" target="_blank">Lire l'article original</a>
                </div>
            </div>"""
            articles_html.append(article_html)
        
        # Main HTML template
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Better French v5 - Autonomous & Intelligent</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        .v5-features {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            color: white;
        }}
        .articles-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .article-card {{
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .article-card h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        .summary {{
            font-size: 16px;
            line-height: 1.6;
            color: #34495e;
            margin-bottom: 20px;
        }}
        .vocabulary-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .vocabulary-section h3 {{
            color: #28a745;
            margin-bottom: 15px;
        }}
        .vocabulary-item {{
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }}
        .article-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
        }}
        .article-meta a {{
            color: #007bff;
            text-decoration: none;
        }}
        .article-meta a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Better French v5 - Autonomous System</h1>
        <p>Apprentissage du français avec une curation intelligente et autonome</p>
    </div>
    
    <div class="v5-features">
        <h2>🚀 Innovation v5:</h2>
        <ul>
            <li>✅ Scraper autonome (toutes les heures)</li>
            <li>✅ Sélection par IA (Gemini 2.5 Flash)</li>
            <li>✅ Pipeline V3 + V4 intégré</li>
            <li>✅ Architecture séparée (scraper + processeur)</li>
            <li>✅ Curation intelligente anti-spam</li>
        </ul>
        <p><strong>Résultat:</strong> Contenu de qualité, diversifié, mis à jour automatiquement</p>
    </div>
    
    <div class="articles-container">
        <h2 style="color: white; text-align: center;">📰 Articles d'Aujourd'hui ({len(articles)} articles)</h2>
        {''.join(articles_html)}
    </div>
    
    <div style="text-align: center; color: white; margin-top: 40px;">
        <p>Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M')} UTC</p>
        <p>🤖 Système autonome v5 - Zéro intervention manuelle</p>
    </div>
</body>
</html>"""
        
        # Save HTML file
        html_file = website_dir / 'index.html'
        html_file.write_text(html_content, encoding='utf-8')
        
        print(f"📝 Website HTML generated: {html_file}") 