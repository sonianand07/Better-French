#!/usr/bin/env python3
"""
Better French Max - Cost-Optimized AI Processor
Inherits exact AI processing logic from proven manual system
Enhanced with batch processing and cost optimization for automation
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import re
# spaCy NER for robust name detection
try:
    import spacy
    _NLP_EN = spacy.load("en_core_web_sm", disable=["tagger", "parser"])
    _NLP_FR = spacy.load("fr_core_news_sm", disable=["tagger", "parser"])
except Exception:
    _NLP_EN = _NLP_FR = None

# Ensure project root is on PYTHONPATH so we can import 'config.*' and 'automation'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    # Debug: confirm path addition
    # print(f"🔧 Added PROJECT_ROOT to sys.path: {PROJECT_ROOT}")

# Import automation config with fallback
try:
    from automation import AUTOMATION_CONFIG  # type: ignore
except ModuleNotFoundError:
    from config.automation import AUTOMATION_CONFIG  # type: ignore
    # Expose under top-level name so downstream modules behave the same
    import importlib, sys as _sys
    _sys.modules['automation'] = importlib.import_module('config.automation')

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ProcessedArticle:
    """AI-processed article with enhanced learning content"""
    # Original article information
    original_article_title: str
    original_article_link: str
    original_article_published_date: str
    source_name: str
    
    # Quality scores (from curation)
    quality_scores: Dict[str, float]
    
    # AI-enhanced content for learning
    simplified_french_title: str
    simplified_english_title: str
    french_summary: str
    english_summary: str
    
    # Enhanced learning features
    contextual_title_explanations: List[Dict[str, str]]  # Detailed word-by-word explanations
    key_vocabulary: List[Dict[str, str]]                 # Important vocabulary from article
    cultural_context: Dict[str, str]                     # Cultural and practical context
    
    # Processing metadata
    processed_at: str
    processing_id: str
    curation_metadata: Dict[str, Any]
    
    # Cost tracking
    api_calls_used: int = 1
    processing_cost: float = 0.0

class CostOptimizedAIProcessor:
    """
    Cost-optimized AI processor for Better French Max
    Processes only top-quality articles in batches for maximum efficiency
    Inherits exact logic from proven manual system
    """
    
    def __init__(self):
        self.ai_config = AUTOMATION_CONFIG['ai_processing']
        self.cost_config = AUTOMATION_CONFIG['cost']
        
        # OpenRouter configuration (same as manual system)
        # First try environment variable, then fall back to config file
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            # Import and set from config file  
            try:
                import config.api_config
                config.api_config.setup_environment_variables()
                self.api_key = os.getenv('OPENROUTER_API_KEY')
                logger.info("✅ API key loaded from config file")
            except ImportError:
                logger.error("❌ Could not import API config")
        
        if not self.api_key:
            logger.error("❌ OpenRouter API key not found in environment variables or config")
            raise ValueError("OpenRouter API key is required")
        else:
            logger.info(f"✅ OpenRouter API key configured (length: {len(self.api_key)} chars)")
        
        self.api_base_url = "https://openrouter.ai/api/v1"
        self.model = self.ai_config['model']
        
        # Cost tracking
        self.daily_cost = 0.0
        self.daily_api_calls = 0
        self.batch_results = []
        
        # Processing statistics
        self.processing_stats = {
            'articles_processed_today': 0,
            'total_cost_today': 0.0,
            'average_processing_time': 0.0,
            'success_rate': 100.0,
            'failed_articles': []
        }
        
        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://better-french-max.com',
            'X-Title': 'Better French Max - Automated AI Processing'
        })
        
        # Debug: Log the authorization header (without revealing the full key)
        auth_header = self.session.headers.get('Authorization', '')
        if auth_header:
            logger.info(f"✅ Authorization header set: {auth_header[:20]}...{auth_header[-10:]}")
        else:
            logger.error("❌ Authorization header not set!")
        
        logger.info("🤖 Cost-Optimized AI Processor initialized")
        logger.info(f"📊 Model: {self.model}")
        logger.info(f"💰 Daily budget: ${self.cost_config['daily_cost_limit']}")
        logger.info(f"📄 Max articles per day: {self.cost_config['max_ai_articles_per_day']}")
    
    def check_cost_limits(self) -> Tuple[bool, str]:
        """Check if we're within cost limits before processing"""
        if self.daily_cost >= self.cost_config['daily_cost_limit']:
            return False, f"Daily cost limit reached: ${self.daily_cost:.2f}"
        
        if self.daily_api_calls >= self.cost_config['max_ai_calls_per_day']:
            return False, f"Daily API call limit reached: {self.daily_api_calls}"
        
        return True, "Within limits"
    
    def _merge_proper_nouns(self, text: str) -> str:
        """Merge 2-5 consecutive capitalised tokens (names, places) into one phrase.

        Heuristic rules:
        • A token is considered *cap-initial* when its first char is A-Z.
        • Internal hyphens, apostrophes or periods inside the token are allowed (Jean-Luc, O'Neill, J.).
        • Digits inside the token break the run.
        • Merge runs of length 2-5; single tokens are left untouched; runs >5 are rare and skipped to
          avoid over-merging lists.
        """
        if not text:
            return text

        tokens: List[str] = text.split()
        merged: List[str] = []
        i = 0
        while i < len(tokens):
            run: List[str] = []

            def _is_cap_token(tok: str) -> bool:
                tok = tok.rstrip('.,:;!?')
                if not tok or not tok[0].isupper():
                    return False
                # Allow hyphen, apostrophe, period inside but no digits
                return all(c.isalpha() or c in "-.''" for c in tok)

            while i < len(tokens) and _is_cap_token(tokens[i]):
                run.append(tokens[i].rstrip('.,:;!?'))
                i += 1
                if len(run) == 5:
                    break

            if 2 <= len(run) <= 5:
                merged.append(" ".join(run))
            else:
                # Not a valid run; push back tokens as-is
                if run:
                    merged.extend(run)
                else:
                    merged.append(tokens[i])
                    i += 1

        return " ".join(merged)

    def create_ai_prompt(self, article: Dict[str, Any]) -> str:
        """Create comprehensive AI prompt for all required outputs"""
        
        # Extract article data
        original_title = article.get('title') or article.get('original_data', {}).get('title', '')
        original_title = self._merge_proper_nouns(original_title)
        summary = article.get('summary') or article.get('original_data', {}).get('summary', '')
        content = article.get('content', '')
        
        # Use the exact few-shot examples from the proven system
        few_shot_examples = self._get_few_shot_examples()

        # New examples (1 title pair + 5 summaries, 30-40 words each)
        simplified_examples = """
TITLE EXAMPLE
Original Title: Inflation : les prix alimentaires vont-ils enfin baisser ?
"simplified_french_title": "Inflation : les prix alimentaires vont-ils enfin baisser ?"  # 57 chars
"simplified_english_title": "Inflation: Will food prices finally fall?"  # 48 chars

SUMMARY EXAMPLE 1 (FR & EN, 34 / 35 words)
"french_summary": "La nouvelle loi climat oblige les grandes entreprises à publier chaque année un bilan carbone détaillé. Des ONG saluent un pas majeur, mais avertissent que des contrôles sérieux seront essentiels pour éviter le greenwashing."
"english_summary": "A new climate law forces large companies to publish an annual, detailed carbon report. NGOs welcome the major step yet warn that strong enforcement is crucial to stop firms from green-washing their public image."

SUMMARY EXAMPLE 2 (32 / 33 words)
"french_summary": "Après deux semaines de grève, la SNCF accepte une hausse salariale de 4 %. Les syndicats considèrent l'accord comme une première victoire et suspendent le mouvement pour laisser place aux négociations sectorielles."
"english_summary": "After two weeks of strikes, French Railways agreed to a 4 % pay rise. Unions call the deal an initial victory and pause the stoppage, opening room for detailed talks in each job category."

SUMMARY EXAMPLE 3 (37 / 36 words)
"french_summary": "Le Parlement européen interdit dès 2035 la vente de voitures diesel et essence neuves. Les constructeurs saluent une visibilité claire, mais s'inquiètent du retard des bornes de recharge dans plusieurs États membres."
"english_summary": "The European Parliament has banned sales of new petrol and diesel cars from 2035. Carmakers welcome the clear timeline yet worry many member states still lag in building a dense fast-charging network."

SUMMARY EXAMPLE 4 (31 / 32 words)
"french_summary": "Un séisme de magnitude 6,2 a frappé le sud du Chili sans faire de victime grave. Les autorités rappellent cependant l'importance de renforcer les bâtiments anciens situés dans les zones sismiques."
"english_summary": "A 6.2-magnitude earthquake shook southern Chile causing no serious casualties. Officials nevertheless stress the urgent need to reinforce older buildings that sit in the country's high-risk seismic corridor."

SUMMARY EXAMPLE 5 (35 / 34 words)
"french_summary": "La finale de Roland-Garros se jouera finalement sous le toit fermé à cause d'orages annoncés. Les organisateurs assurent que cette décision garantit la sécurité du public tout en préservant la qualité du jeu."
"english_summary": "The French Open final will be played under the closed roof because thunderstorms are forecast. Organisers say the move protects spectators' safety while ensuring consistent playing conditions for the athletes."
"""

        # COMPREHENSIVE prompt for all outputs
        full_prompt = f"""{few_shot_examples}
{simplified_examples}

Please analyze the following French news article and provide ALL the following outputs:

Original Title: {original_title}
Original Summary: {summary}

Provide your response as a VALID JSON object with these exact keys:

{{
  "simplified_french_title": "[Create a simplified French version of the title, removing complex phrases while keeping the meaning]",
  "simplified_english_title": "[Create a clear English translation of the title]", 
  "french_summary": "[Create a simple French summary in exactly 20-25 words using basic vocabulary]",
  "english_summary": "[Create a clear English summary in exactly 20-25 words]",
  "contextual_title_explanations": [
    {{
      "original_word": "[exact word/phrase from title]",
      "display_format": "**[Word]:** [Brief translation]",
      "explanation": "[Detailed explanation in English]",
      "cultural_note": "[Cultural context if relevant: historical significance, political context, French cultural aspects, or current events connection. Empty string if not applicable]",
      "part_of_speech": "[Part of speech of the word]",
      "cefr": "[CEFR level of the word]",
      "example": "[One short sentence, max 10 words, showing the word in context]"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Only return the JSON object, no other text
- Make simplified titles clear and accessible  
- Simplified titles must be ≤ 60 characters, keep all key actors/action/place, remove click-bait prefixes and quotes, keep original tense.
- If the original headline names a speaker or source (text before the first colon or within quotes), retain that attribution in the simplified titles.
- Preserve important scope words such as "régional", "mondial", etc.
- YOU MUST provide contextual explanations for EVERY SINGLE WORD AND PHRASE in the title - NO EXCEPTIONS
- This includes: articles (le, la, une), prepositions (de, à, dans, pour), conjunctions (et, que, ou), pronouns (ce, l', on), basic verbs (est, sait), and ALL other words
- EVERY word helps language learners understand grammar patterns and build vocabulary
- When a proper noun consists of multiple capitalised words (e.g., "Donald Trump", "David A. Bell"), treat the entire name as **one** original_word and provide one combined explanation – do NOT split names into separate words
- Even if a word seems "basic", it must be explained for learners at different proficiency levels
- Punctuation **also** needs context: include brief usage notes for any punctuation marks appearing in the title (e.g., ":" colon introduces a clause, "," comma separates elements, "?" indicates a question) – double-check that commas, colons, slashes, hyphens, and question marks are not skipped.
- FULL PUNCTUATION WHITELIST: you must add an entry for **each** occurrence of these characters if they appear in the title → . , ; : ! ? … — - / ( ) « » " ' ’
- COVERAGE CHECK: If the number of objects in "contextual_title_explanations" is **not exactly equal** to the number of tokens (INCLUDING punctuation) in the original title, you must instead reply with ONLY the single word **ERROR**.
- For **every** original_word you must add three extra teaching fields inside its JSON object:
   • "part_of_speech"  (noun, verb, adj., etc.)
   • "cefr"  (A1, A2, B1, B2, C1, C2)
   • "example"  (ONE short sentence, max 10 words, showing the word in context)
- Do NOT skip any words - complete coverage is mandatory
- Ensure all French text uses proper accents and grammar
- Hyphenated or slash-separated compounds (e.g., "Seine-Saint-Denis", "top/flop", "13/06") must be treated as **one** original_word – do NOT split on the hyphen or slash.
- Contractions that use an apostrophe (straight ' or curly ’) such as "L'Iran", "n'est", "l'inauguration" must likewise be **one** original_word.
- When punctuation appears *inside* such a compound/contraction, do **not** create a separate entry for that punctuation – the context belongs to the full word.

Based on the article above, provide the complete JSON response:
"""
        
        return full_prompt

    # ------------------------------------------------------------------
    # NEW: two-step prompting helpers (titles+summaries, explanations)
    # ------------------------------------------------------------------

    def build_title_prompt(self, article: Dict[str, Any]) -> str:
        """Return prompt asking only for simplified titles and 20-25-word summaries."""
        original_title = article.get('title') or article.get('original_data', {}).get('title', '')
        original_title = self._merge_proper_nouns(original_title)
        summary = article.get('summary') or article.get('original_data', {}).get('summary', '')

        # Explicit JSON schema that the model must follow
        json_schema = (
            '{\n'
            '  "simplified_french_title": "",\n'
            '  "simplified_english_title": "",\n'
            '  "french_summary": "",\n'
            '  "english_summary": ""\n'
            '}'
        )

        return (
            "You are Better French assistant. Return ONLY a VALID JSON object exactly matching this schema:\n"
            f"{json_schema}\n"
            "DO NOT add any other keys or explanatory text.\n\n"
            "Key requirements:\n"
            "  • simplified_french_title – concise French ≤ 60 chars, keep speaker & scope.\n"
            "  • simplified_english_title – faithful English translation ≤ 60 chars.\n"
            "  • french_summary – simple French, 30-40 words – count them.\n"
            "  • english_summary – clear English, 30-40 words – count them.\n"
            "Rules for titles: preserve actors/places/actions, drop click-bait prefixes, maintain tense.\n\n"
            f"Original Title: {original_title}\n"
            f"Original Summary: {summary}"
        )

    def build_explanation_prompt(self, article: Dict[str, Any]) -> str:
        """Prompt that asks only for contextual_title_explanations covering every token."""
        original_title = article.get('title') or article.get('original_data', {}).get('title', '')
        original_title = self._merge_proper_nouns(original_title)
        few_shot = self._get_few_shot_examples()
        json_schema = '[\n  {\n    "original_word": "",\n    "display_format": "",\n    "explanation": "",\n    "cultural_note": "",\n    "part_of_speech": "",\n    "cefr": "",\n    "example": ""\n  }\n]'

        name_rule = (
            "IMPORTANT : treat a person's full name (all consecutive capitalised words, including hyphens, apostrophes or middle initials) as **one** original_word."
        )

        name_examples = """
EX 1 — simple two-word name
Title: "Donald Trump promet un accord"
contextual_title_explanations: [ {"original_word": "Donald Trump" , "display_format": "**Donald Trump:** 45e président des États-Unis", "explanation": "American politician and businessman."} ]

EX 2 — hyphenated name
Title: "Jean-Luc Mélenchon critique le budget"
contextual_title_explanations: [ {"original_word": "Jean-Luc Mélenchon", "display_format": "**Jean-Luc Mélenchon:** Chef du parti LFI", "explanation": "French left-wing political leader."} ]

EX 3 — accented first name
Title: "Nicolás Maduro annonce des réformes"
contextual_title_explanations: [ {"original_word": "Nicolás Maduro", "display_format": "**Nicolás Maduro:** Président du Venezuela", "explanation": "Venezuelan head of state."} ]

EX 4 — apostrophe contraction (capital)
Title: "L'Iran répond aux sanctions"
contextual_title_explanations: [ {"original_word": "L'Iran", "display_format": "**L'Iran:** Pays du Moyen-Orient", "explanation": "Middle-Eastern country."} ]

EX 5 — apostrophe contraction (lower-case)
Title: "d'Europe vient une nouvelle directive"
contextual_title_explanations: [ {"original_word": "d'Europe", "display_format": "**d'Europe:** De l'Europe", "explanation": "Refers to Europe as origin."} ]

EX 6 — place name with accent + hyphen
Title: "Sécheresse en Île-de-France cet été"
contextual_title_explanations: [ {"original_word": "Île-de-France", "display_format": "**Île-de-France:** Région de Paris", "explanation": "Region surrounding Paris."} ]

EX 7 — multi-word proper noun with digits
Title: "Les Jeux Olympiques 2024 approchent"
contextual_title_explanations: [ {"original_word": "Jeux Olympiques 2024", "display_format": "**Jeux Olympiques 2024:** Événement sportif mondial", "explanation": "2024 Summer Olympic Games."} ]

EX 8 — punctuation token example
Title: "« Liberté » : un mot chargé d'histoire"
contextual_title_explanations: [ {"original_word": "«", "display_format": "**«:** Guillemets ouvrants", "explanation": "Opening French quotation mark."}, {"original_word": "Liberté", "display_format": "**Liberté:** Freedom", "explanation": "Abstract noun meaning freedom."}, {"original_word": "»", "display_format": "**»:** Guillemets fermants", "explanation": "Closing French quotation mark."}, {"original_word": ":", "display_format": "**:** Deux-points", "explanation": "Colon introducing an explanation."} ]
"""

        return (
            f"{few_shot}\n\n{name_rule}\n\n{name_examples}\n\n"
            "Return ONLY a valid JSON array named contextual_title_explanations exactly matching this template:\n"
            f"{json_schema}\n\n"
            "Requirements: one object per token (word or punctuation), complete coverage.\n"
            f"Title: {original_title}"
        )

    def _get_few_shot_examples(self, num_examples=2):
        """Get comprehensive few-shot examples from the proven original system"""
        # COMPLETE pre_designed_data from the original proven system
        pre_designed_data = {
            "Droits de douane : ces options sur la table de Donald Trump après son revers judiciaire": {
                "contextual_title_explanations": {
                    "Droits de douane": {"display_format": "**Customs Duties / Tariffs:** Taxes on imported goods.", "explanation": "Taxes imposed on goods when they are transported across international borders. Governments usually impose customs duties to protect domestic industries, generate revenue, or regulate the flow of goods.", "cultural_note": "Trade tariffs are a significant tool in international economic policy and can become major points of contention between countries, as seen in various trade disputes involving the US, China, and the EU.", "proficiency_level": "B2"},
                    "ces": {"display_format": "**These:** (demonstrative adjective)", "explanation": "Used to point out specific items or options being discussed.", "cultural_note": "", "proficiency_level": "A1"},
                    "options": {"display_format": "**Options:** Choices or alternatives.", "explanation": "Different courses of action that can be chosen.", "cultural_note": "", "proficiency_level": "A2"},
                    "sur la table": {"display_format": "**On the table:** Under consideration; being discussed or negotiated.", "explanation": "An idiomatic expression meaning that something is available for discussion or is a possibility.", "cultural_note": "Similar to the English idiom 'on the table.'", "proficiency_level": "B1"},
                    "de": {"display_format": "**Of / From:** (preposition)", "explanation": "Indicates possession, origin, or relationship.", "cultural_note": "", "proficiency_level": "A1"},
                    "Donald Trump": {"display_format": "**Donald Trump:** 45th President of the United States.", "explanation": "A prominent American political figure and businessman.", "cultural_note": "His presidency was marked by significant changes to US trade policy, including the imposition of tariffs on goods from various countries.", "proficiency_level": "C1"},
                    "après": {"display_format": "**After:** (preposition)", "explanation": "Indicates something that follows in time.", "cultural_note": "", "proficiency_level": "A1"},
                    "son": {"display_format": "**His / Her / Its:** (possessive adjective)", "explanation": "Indicates possession.", "cultural_note": "", "proficiency_level": "A1"},
                    "revers judiciaire": {"display_format": "**Legal setback / Judicial defeat:** A loss or unfavorable outcome in a court case.", "explanation": "Refers to a situation where a legal case or argument has not been successful.", "cultural_note": "Such setbacks can force a re-evaluation of strategy, as discussed in the article regarding Trump's tariff policies.", "proficiency_level": "B2"}
                }
            },
            "EXCLUSIF. Des cadres des Verts plaident pour adhérer à BDS, mouvement controversé de boycott d'Israël": {
                "contextual_title_explanations": [
                    {"original_word": "EXCLUSIF", "display_format": "**EXCLUSIVE:** (adjective/noun)", "explanation": "Indicates that the information is being reported for the first time by this news outlet.", "cultural_note": "Commonly used in headlines to attract attention."},
                    {"original_word": "Des cadres", "display_format": "**Executives / Leading members / Cadres:** Senior or influential members of an organization.", "explanation": "'Cadre' refers to a manager, executive, or a key member of a political party or organization.", "cultural_note": "In French politics, 'cadres' are the backbone of a party's leadership and decision-making structure."},
                    {"original_word": "des Verts", "display_format": "**Of the Greens (French Green Party):** Refers to the French political party focused on environmental issues (Europe Écologie Les Verts - EELV).", "explanation": "'Les Verts' is the common name for the French Green Party.", "cultural_note": "Like Green parties in other countries, they advocate for ecological policies and often align with left-leaning social stances."},
                    {"original_word": "plaident pour", "display_format": "**Advocate for / Argue in favor of:** To publicly support or recommend a particular cause or policy.", "explanation": "'Plaider' means to plead or argue a case.", "cultural_note": ""},
                    {"original_word": "adhérer à", "display_format": "**To join / To adhere to:** To become a member of or to formally agree to support.", "explanation": "'Adhérer' means to stick to, or in a political context, to join or subscribe to a movement or party.", "cultural_note": ""},
                    {"original_word": "BDS", "display_format": "**BDS (Boycott, Divestment, Sanctions):** A Palestinian-led movement promoting boycotts, divestments, and economic sanctions against Israel.", "explanation": "The movement aims to pressure Israel to meet what it describes as Israel's obligations under international law.", "cultural_note": "BDS is a highly controversial movement, with strong opinions both for and against its methods and goals. Its potential adoption by political parties often sparks significant debate."},
                    {"original_word": "mouvement", "display_format": "**Movement:** A group of people working together to advance their shared political, social, or artistic ideas.", "explanation": "Refers to an organized effort or campaign.", "cultural_note": ""},
                    {"original_word": "controversé", "display_format": "**Controversial:** Giving rise or likely to give rise to public disagreement.", "explanation": "Indicates that the subject is a matter of dispute or strong opinions.", "cultural_note": ""},
                    {"original_word": "de boycott", "display_format": "**Of boycott:** Relating to the act of boycotting.", "explanation": "A boycott is a collective refusal to deal with a person, organization, or country as an expression of protest.", "cultural_note": ""},
                    {"original_word": "d'Israël", "display_format": "**Of Israel:** Relating to the state of Israel.", "explanation": "Referring to the country in the Middle East.", "cultural_note": ""}
                ]
            },
            "Présidentielle en Pologne : l'élection qui donne des sueurs froides à Bruxelles": {
                "contextual_title_explanations": [
                    {"original_word": "Présidentielle", "display_format": "**Presidential (election):** Relating to the election of a president.", "explanation": "Refers to the process of electing a head of state in a republic.", "cultural_note": ""},
                    {"original_word": "en Pologne", "display_format": "**In Poland:** Referring to the country of Poland.", "explanation": "A country in Central Europe.", "cultural_note": "Poland's political direction has significant implications for the European Union, given its size and strategic location."},
                    {"original_word": "l'élection", "display_format": "**The election:** The process of choosing someone for a public office by voting.", "explanation": "A formal and organized choice by vote of a person for a political office or other position.", "cultural_note": ""},
                    {"original_word": "qui donne des sueurs froides", "display_format": "**Which is causing cold sweats / Causing great anxiety:** An idiomatic expression.", "explanation": "Literally 'gives cold sweats,' it means something that causes extreme worry, fear, or anxiety.", "cultural_note": "A common French idiom to express strong apprehension."},
                    {"original_word": "à Bruxelles", "display_format": "**To Brussels (referring to the EU):** Brussels is the de facto capital of the European Union.", "explanation": "When French media mentions 'Bruxelles' in a political context, it often refers to the institutions and decision-making bodies of the European Union.", "cultural_note": "Similar to how 'Washington' is often used to refer to the US federal government."}
                ]
            },
            "Droits de douane : ces cinq petites entreprises qui ont mis un frein à la machine Trump": {
                "contextual_title_explanations": [
                    {"original_word": "Droits de douane", "display_format": "**Customs Duties / Tariffs:** Taxes on imported goods.", "explanation": "Taxes imposed on goods when they are transported across international borders.", "cultural_note": "A recurring theme in trade policy discussions."},
                    {"original_word": "ces cinq petites entreprises", "display_format": "**These five small businesses:** Referring to specific small companies.", "explanation": "'Petites entreprises' are small to medium-sized enterprises (SMEs), often called PME in French.", "cultural_note": "Small businesses are often portrayed as being particularly vulnerable to broad economic policy shifts like tariffs."},
                    {"original_word": "qui ont mis un frein à", "display_format": "**That put a brake on / That slowed down:** An idiomatic expression.", "explanation": "Means to slow down or hinder the progress of something.", "cultural_note": "Similar to the English idiom 'put the brakes on.'"},
                    {"original_word": "la machine Trump", "display_format": "**The Trump machine:** Refers to the administrative and political apparatus of Donald Trump's presidency.", "explanation": "A metaphorical way to describe the functioning and policies of his government.", "cultural_note": "The term 'machine' often implies a powerful, relentless, and somewhat impersonal force."}
                ]
            },
            "Etats-Unis : la Cour d'appel maintient les droits de douane de Donald Trump": {
                "contextual_title_explanations": [
                    {"original_word": "Etats-Unis", "display_format": "**United States:** Referring to the United States of America.", "explanation": "Country in North America.", "cultural_note": ""},
                    {"original_word": "la Cour d'appel", "display_format": "**The Court of Appeal / Appeals Court:** A court that hears appeals from lower court decisions.", "explanation": "A higher court that reviews the decisions of trial courts or other lower courts.", "cultural_note": "An essential part of the judicial process, allowing for review and potential correction of legal errors."},
                    {"original_word": "maintient", "display_format": "**Maintains / Upholds:** To keep in an existing state; to preserve from failure or decline.", "explanation": "In a legal context, it means to affirm or keep a previous decision or state of affairs in place.", "cultural_note": ""},
                    {"original_word": "les droits de douane", "display_format": "**The customs duties / The tariffs:** Taxes on imported goods.", "explanation": "Taxes imposed on goods when they are transported across international borders.", "cultural_note": ""},
                    {"original_word": "de Donald Trump", "display_format": "**Of Donald Trump:** Belonging to or enacted by Donald Trump.", "explanation": "Refers to policies associated with his presidency.", "cultural_note": ""}
                ]
            },
            "Guerre à Gaza : Benyamin Netanyahou, le grand divorce avec les Israéliens": {
                "contextual_title_explanations": [
                    {"original_word": "Guerre à Gaza", "display_format": "**War in Gaza:**", "explanation": "Refers to the conflict in the Gaza Strip.", "cultural_note": "Long-standing conflict with global repercussions."},
                    {"original_word": "Benyamin Netanyahou", "display_format": "**Benjamin Netanyahu:**", "explanation": "Prime Minister of Israel.", "cultural_note": "A polarizing political figure."},
                    {"original_word": "le grand divorce", "display_format": "**The great divorce:**", "explanation": "Metaphor for a major split or estrangement.", "cultural_note": "Often used to describe political rifts."},
                    {"original_word": "avec les Israéliens", "display_format": "**With the Israelis:**", "explanation": "Refers to the people of Israel.", "cultural_note": ""}
                ]
            },
            "PS : les députés de Seine-Saint-Denis boycotteront l'inauguration": {
                "contextual_title_explanations": [
                    {"original_word": "PS", "display_format": "**PS (Parti socialiste):**", "explanation": "French Socialist Party.", "cultural_note": "A major centre-left political party in France."},
                    {"original_word": ":", "display_format": "**Colon:**", "explanation": "Introduces an explanation.", "cultural_note": ""},
                    {"original_word": "les", "display_format": "**The:** (article)", "explanation": "Definite article used before plural nouns.", "cultural_note": ""},
                    {"original_word": "députés", "display_format": "**Deputies:**", "explanation": "Members of the National Assembly.", "cultural_note": "French parliamentarians."},
                    {"original_word": "de", "display_format": "**Of / from:**", "explanation": "Preposition indicating origin or possession.", "cultural_note": ""},
                    {"original_word": "Seine-Saint-Denis", "display_format": "**Seine-Saint-Denis:**", "explanation": "A department north of Paris.", "cultural_note": "Often referenced in socio-economic discussions."},
                    {"original_word": "boycotteront", "display_format": "**Will boycott:**", "explanation": "Future tense of 'boycotter'.", "cultural_note": ""},
                    {"original_word": "l'inauguration", "display_format": "**The inauguration:**", "explanation": "Official opening event.", "cultural_note": "Contraction kept as one token as required."}
                ]
            },
            "Face à la Chine, l'Europe en quête d'une nouvelle stratégie industrielle": {
                "contextual_title_explanations": [
                    {"original_word": "Face à la Chine", "display_format": "**Facing China / In response to China:** Indicates a reaction or positioning relative to China.", "explanation": "Highlights the challenges or competition posed by China.", "cultural_note": "China's rise as a global economic power is a central theme in international relations and economic policy discussions in Europe."},
                    {"original_word": "l'Europe", "display_format": "**Europe (often referring to the EU):** The continent, but in policy contexts, usually means the European Union.", "explanation": "The European Union as a political and economic entity.", "cultural_note": ""},
                    {"original_word": "en quête d'une", "display_format": "**In search of a / Seeking a:** Looking for or trying to find something.", "explanation": "", "cultural_note": ""},
                    {"original_word": "nouvelle stratégie industrielle", "display_format": "**New industrial strategy:** A revised plan concerning a country's or region's manufacturing and industrial sectors.", "explanation": "Refers to policies aimed at promoting industrial growth, innovation, and competitiveness.", "cultural_note": "Industrial strategy is a key area of EU policy as it seeks to maintain its economic standing."}
                ]
            },
            "IA générative : pourquoi la France est en train de perdre la bataille face aux Etats-Unis": {
                "contextual_title_explanations": [
                    {"original_word": "IA générative", "display_format": "**Generative AI:** Artificial Intelligence that can create new content.", "explanation": "A subset of AI that can generate text, images, audio, and other media in response to prompts.", "cultural_note": "A rapidly advancing field with significant economic and societal implications, dominated by major US tech companies but with active research and development globally."},
                    {"original_word": "pourquoi la France est en train de perdre la bataille", "display_format": "**Why France is losing the battle:** Explores the reasons behind France's perceived disadvantage.", "explanation": "Suggests a competitive struggle where France is not succeeding.", "cultural_note": "There's often a public debate in France about its technological competitiveness, particularly vis-à-vis the US and China."},
                    {"original_word": "face aux Etats-Unis", "display_format": "**Against the United States / Compared to the United States:** Highlighting the US as the primary competitor or benchmark.", "explanation": "", "cultural_note": ""}
                ]
            },
            "Réforme des retraites : le gouvernement face au mur de la dette": {
                "contextual_title_explanations": [
                    {"original_word": "Réforme des retraites", "display_format": "**Pension Reform:** Changes to the national retirement system.", "explanation": "Refers to government policies aimed at modifying how pensions are funded, calculated, and when people can retire.", "cultural_note": "Pension reform is a highly sensitive and frequently debated political issue in France, often leading to widespread protests and strikes."},
                    {"original_word": "le gouvernement", "display_format": "**The government:** The ruling administration.", "explanation": "The executive branch of the French state.", "cultural_note": ""},
                    {"original_word": "face au mur de la dette", "display_format": "**Facing the debt wall:** Confronting a significant and challenging level of national debt.", "explanation": "The 'wall' metaphor emphasizes the difficulty and scale of the problem.", "cultural_note": "France, like many developed countries, has a substantial national debt, and its management is a constant concern for policymakers."}
                ]
            },
            "Inflation : les prix alimentaires vont-ils enfin baisser ?": {
                "contextual_title_explanations": [
                    {"original_word": "Inflation", "display_format": "**Inflation:** The rate at which the general level of prices for goods and services is rising.", "explanation": "A key economic indicator reflecting the erosion of purchasing power.", "cultural_note": "High inflation, especially for essential goods like food, is a major concern for the public and policymakers."},
                    {"original_word": "les prix alimentaires", "display_format": "**Food prices:** The cost of food items.", "explanation": "", "cultural_note": ""},
                    {"original_word": "vont-ils enfin baisser ?", "display_format": "**Will they finally decrease? / Are they finally going to go down?:** Expresses a sense of anticipation or hope for a reduction.", "explanation": "The word 'enfin' (finally) suggests a period of waiting or suffering high prices.", "cultural_note": ""}
                ]
            },
            "Climat : la France peut-elle atteindre ses objectifs de réduction d'émissions ?": {
                "contextual_title_explanations": [
                    {"original_word": "Climat", "display_format": "**Climate:** Referring to climate change.", "explanation": "The long-term alteration of temperature and typical weather patterns in a place.", "cultural_note": "Climate change is a major global concern, and countries have set targets to reduce their impact."},
                    {"original_word": "la France peut-elle atteindre", "display_format": "**Can France achieve / Can France reach:** Questions the feasibility of achieving a goal.", "explanation": "", "cultural_note": ""},
                    {"original_word": "ses objectifs de réduction d'émissions ?", "display_format": "**Its emission reduction targets?:** The specific goals set for lowering greenhouse gas output.", "explanation": "These targets are often part of national or international agreements like the Paris Agreement.", "cultural_note": "Meeting these targets requires significant policy changes and investments."}
                ]
            },
            "JO 2024 : à un an de l'événement, Paris est-elle prête ?": {
                "contextual_title_explanations": [
                    {"original_word": "JO 2024", "display_format": "**2024 Olympics (Jeux Olympiques):** Referring to the Olympic Games scheduled for 2024.", "explanation": "'JO' is the common French abbreviation for 'Jeux Olympiques'.", "cultural_note": "Hosting the Olympics is a major undertaking for any city, involving massive investment and global attention. Paris 2024 is a significant national project for France."},
                    {"original_word": "à un an de l'événement", "display_format": "**One year from the event / With one year to go:** Marking the one-year countdown.", "explanation": "", "cultural_note": ""},
                    {"original_word": "Paris est-elle prête ?", "display_format": "**Is Paris ready?:** Questions the city's state of preparedness.", "explanation": "", "cultural_note": "Media scrutiny of Olympic preparations typically intensifies as the event approaches."}
                ]
            }
        }
        
        # Select examples for few-shot prompting
        example_keys = list(pre_designed_data.keys())
        selected_examples = []
        for i in range(min(num_examples, len(example_keys))):
            key = example_keys[i]
            data = pre_designed_data[key]
            example_str = f"EXAMPLE {i+1}:\nOriginal Title: \"{key}\"\nContextual Title Explanations (JSON format):\n{json.dumps(data['contextual_title_explanations'], ensure_ascii=False, indent=2)}\n---\n"
            selected_examples.append(example_str)
        return "\n".join(selected_examples)
    
    def call_openrouter_api(self, prompt: str, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call OpenRouter API with the exact approach from original system"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI assistant for 'Better French'. Your goal is to help non-native French speakers understand complex French news articles. Provide clear, concise, and accurate information. For contextual explanations, provide them in a valid JSON list format as specified in the examples."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Allow the model to finish the long JSON with POS/CEFR/example + punctuation entries.
                # 3 000 output tokens stays inexpensive on Llama-3 and prevents truncation.
                "max_tokens": 3000,
                "temperature": 0.7
            }
            
            response = self.session.post(
                f"{self.api_base_url}/chat/completions",
                json=payload,
                timeout=30
            )
            
            # ------------------------------------------------------------------
            # §1  Non-200 HTTP → log and abort this call
            # ------------------------------------------------------------------
            if response.status_code != 200:
                logger.error(f"❌ OpenRouter HTTP {response.status_code}: {response.text[:200]}…")
                return (None, 0.0)
            
            # ------------------------------------------------------------------
            # §2  Safe JSON decode. Some error pages are still 200 w/ HTML.
            # ------------------------------------------------------------------
            try:
                result = response.json()
            except ValueError:
                logger.error("❌ OpenRouter returned non-JSON payload (first 200 chars shown) → %s…", response.text[:200])
                return (None, 0.0)
            
            # ------------------------------------------------------------------
            # From here we assume 'result' is a proper dict from the API
            # ------------------------------------------------------------------

            # Track costs with accurate OpenRouter pricing FIRST
            usage = result.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
            
            # --- Dynamic cost table so model swaps don't require code edits elsewhere ---
            PRICE_TABLE = {
                "anthropic/claude-3.5-sonnet":      (0.00300, 0.01500),  # $3 / $15 per 1M
                "meta-llama/llama-3-70b-instruct": (0.00035, 0.00070),  # $0.35 / $0.70 per 1M
                "google/gemini-2-flash":            (0.00025, 0.00050),
                # Add new models here ➜ "vendor/model": (in_cost, out_cost)
            }

            # Fallback: default to Sonnet rates if unknown model string
            input_cost_per_1k, output_cost_per_1k = PRICE_TABLE.get(
                self.model,
                PRICE_TABLE.get("anthropic/claude-3.5-sonnet")
            )
            
            # Calculate actual cost
            input_cost = (input_tokens / 1000) * input_cost_per_1k
            output_cost = (output_tokens / 1000) * output_cost_per_1k
            article_cost = input_cost + output_cost
            
            self.daily_cost += article_cost
            self.daily_api_calls += 1
            
            # Log detailed cost info
            logger.info(f"💰 API Usage: {input_tokens} input + {output_tokens} output = {total_tokens} total tokens")
            logger.info(f"💰 Article cost: ${article_cost:.4f} (${input_cost:.4f} input + ${output_cost:.4f} output)")
            logger.info(f"💰 Running total today: ${self.daily_cost:.4f}")
            
            # Extract AI response
            ai_content = result['choices'][0]['message']['content'].strip()
            logger.info(f"🤖 AI raw response length: {len(ai_content)} characters")
            
            # Try robust JSON extraction ➜ tolerate leading prose / ``` fences / trailing text
            parsed_json = self._safe_json_loads(ai_content)
            if parsed_json is None:
                logger.warning("⚠️ Could not extract JSON from AI response (first 120 chars shown) → %s…", ai_content[:120])
                return (None, article_cost)
            
            # Accept both dict and list top-level shapes
            if isinstance(parsed_json, list):
                ai_result = {
                    "contextual_title_explanations": parsed_json,
                    "key_vocabulary": [],
                    "cultural_context": {}
                }
            else:
                ai_result = parsed_json
            
            return (ai_result, article_cost)
            
        except requests.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error calling OpenRouter API: {e}")
            return None
    
    def _extract_explanations_manually(self, ai_content: str) -> List[Dict[str, str]]:
        """Manually extract contextual explanations from malformed AI response"""
        explanations = []
        
        try:
            # Look for contextual_title_explanations section
            start_marker = '"contextual_title_explanations":'
            start_idx = ai_content.find(start_marker)
            if start_idx == -1:
                return []
            
            # Find the start of the array
            array_start = ai_content.find('[', start_idx)
            if array_start == -1:
                return []
            
            # Find the matching closing bracket
            bracket_count = 0
            array_end = array_start
            for i, char in enumerate(ai_content[array_start:]):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        array_end = array_start + i + 1
                        break
            
            # Extract just the explanations array
            explanations_text = ai_content[array_start:array_end]
            explanations = json.loads(explanations_text)
            
            logger.info(f"🔧 Successfully extracted {len(explanations)} explanations manually")
            return explanations
            
        except Exception as e:
            logger.error(f"❌ Manual extraction failed: {e}")
            return []
    
    def process_single_article(self, scored_article: Dict[str, Any]) -> Optional[ProcessedArticle]:
        """Process a single article with AI enhancement"""
        try:
            start_time = time.time()  # Track processing duration per article

            # STEP 1: Get simplified titles and summaries
            title_prompt = self.build_title_prompt(scored_article)
            ai_titles_resp = self.call_openrouter_api(title_prompt, scored_article)
            if not ai_titles_resp or ai_titles_resp[0] is None:
                logger.error("❌ AI title+summary call failed for: %s", scored_article.get('title'))
                return None
            ai_titles, cost_titles = ai_titles_resp

            # ------------------------------------------------------------------
            # Validate summary word count (30-40). If out of range, retry once.
            # ------------------------------------------------------------------
            def _wcount(txt):
                import re, textwrap
                return len(re.findall(r"\\w+", txt or ""))

            needs_retry = False
            for key in ("french_summary", "english_summary"):
                wc = _wcount(ai_titles.get(key, ""))
                if wc < 30 or wc > 40:
                    needs_retry = True
                    logger.info(f"⚠️ {key} word-count {wc} out of range – will retry once")
                    break

            if needs_retry:
                retry_resp = self.call_openrouter_api(title_prompt, scored_article)
                if retry_resp and retry_resp[0]:
                    ai_titles, add_cost = retry_resp
                    cost_titles += add_cost

            # Enforce 60-char limit on simplified titles (truncate with …)
            for key in ("simplified_french_title", "simplified_english_title"):
                title_txt = ai_titles.get(key, "")
                if len(title_txt) > 60:
                    ai_titles[key] = title_txt[:57].rstrip() + "…"

            # Merge back into article dict for later saving
            scored_article.update({
                'simplified_french_title': ai_titles.get('simplified_french_title', ''),
                'simplified_english_title': ai_titles.get('simplified_english_title', ''),
                'french_summary': ai_titles.get('french_summary', ''),
                'english_summary': ai_titles.get('english_summary', ''),
            })

            # STEP 2: Get contextual explanations
            explain_prompt = self.build_explanation_prompt(scored_article)
            retries = 0
            max_retries = 1
            while True:
                ai_content_resp = self.call_openrouter_api(explain_prompt, scored_article)
                if not ai_content_resp or ai_content_resp[0] is None:
                    logger.error("❌ AI explanation call failed for: %s", scored_article.get('title'))
                    return None
                ai_content, cost_explain = ai_content_resp

                # ---------------- Inline validation: names & contractions ----------------
                def _expected_tokens(title: str):
                    import re
                    merged_title = self._merge_proper_nouns(title)
                    tokens = merged_title.split()
                    expect = []
                    # collect multi-word proper nouns (spaces)
                    for tok in tokens:
                        if ' ' in tok:
                            expect.append(tok)
                    # collect apostrophe contractions l'Iran etc.
                    expect.extend(re.findall(r"\b\w+'\w+", merged_title))
                    return set(expect)

                title_src = scored_article.get('title') or scored_article.get('original_data', {}).get('title', '')
                expected = _expected_tokens(title_src)
                expected.update(self._spacy_entities(title_src))  # spaCy NER supplement
                provided = set()
                if isinstance(ai_content.get('contextual_title_explanations'), list):
                    provided = {e.get('original_word') for e in ai_content['contextual_title_explanations']}
                elif isinstance(ai_content.get('contextual_title_explanations'), dict):
                    provided = set(ai_content['contextual_title_explanations'].keys())

                missing = [t for t in expected if (" " in t or "'" in t) and t not in provided]

                if not missing or retries >= max_retries:
                    break  # accept result

                # Retry once with explicit correction prompt
                logger.info(f"🔄 Retry explanation: missing tokens {missing}")
                explain_prompt = (
                    f"Your previous answer missed these tokens or split them: {', '.join(missing)}. "
                    f"Return corrected contextual_title_explanations JSON array ONLY, full coverage. Title: {title_src}"
                )
                retries += 1

            # Extract original article data
            if 'original_data' in scored_article:
                original_data = scored_article['original_data']
                quality_scores = {
                    'quality_score': scored_article.get('quality_score', 0),
                    'relevance_score': scored_article.get('relevance_score', 0),
                    'importance_score': scored_article.get('importance_score', 0),
                    'total_score': scored_article.get('total_score', 0)
                }
            else:
                original_data = scored_article
                quality_scores = {}

            # Total cost for this article (two API calls)
            article_processing_cost = cost_titles + cost_explain

            # Create processed article
            processed = ProcessedArticle(
                original_article_title=original_data.get('title', ''),
                original_article_link=original_data.get('link', ''),
                original_article_published_date=original_data.get('published', ''),
                source_name=original_data.get('source_name', ''),
                quality_scores=quality_scores,
                simplified_french_title=scored_article.get('simplified_french_title', ''),
                simplified_english_title=scored_article.get('simplified_english_title', ''),
                french_summary=scored_article.get('french_summary', ''),
                english_summary=scored_article.get('english_summary', ''),
                contextual_title_explanations=ai_content.get('contextual_title_explanations', []),
                key_vocabulary=ai_content.get('key_vocabulary', []),
                cultural_context=ai_content.get('cultural_context', {}),
                processed_at=datetime.now(timezone.utc).isoformat(),
                processing_id=f"ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(original_data.get('link', '')) % 10000}",
                curation_metadata={
                    'curation_id': scored_article.get('curation_id', ''),
                    'curated_at': scored_article.get('curated_at', ''),
                    'fast_tracked': scored_article.get('fast_tracked', False)
                },
                api_calls_used=2,
                processing_cost=article_processing_cost
            )

            # Update statistics
            self.processing_stats['articles_processed_today'] += 1
            self.processing_stats['total_cost_today'] = self.daily_cost
            self.processing_stats['average_processing_time'] = (
                (self.processing_stats['average_processing_time'] * (self.processing_stats['articles_processed_today'] - 1) + (time.time() - start_time)) /
                self.processing_stats['articles_processed_today']
            )

            logger.info(f"✨ AI processed: {processed.simplified_french_title[:50]}...")
            logger.debug(f"💰 Cost: ${processed.processing_cost:.4f}, Time: {time.time() - start_time:.2f}s")

            return processed
            
        except Exception as e:
            logger.error(f"❌ Failed to process article: {e}")
            self.processing_stats['failed_articles'].append({
                'title': original_data.get('title', 'Unknown')[:50],
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return None
    
    def is_article_already_processed(self, article_data: Dict[str, Any]) -> bool:
        """Check if an article has already been AI-processed to avoid duplicate spending"""
        try:
            # Check if article already has AI enhancement flags
            if article_data.get('ai_enhanced', False):
                return True
            
            # Check if it has contextual explanations (main AI feature)
            if article_data.get('contextual_title_explanations'):
                return True
            
            # Check for AI-specific fields
            if (article_data.get('simplified_french_title') and 
                article_data.get('simplified_english_title') and
                article_data.get('english_summary') and
                article_data.get('french_summary')):
                return True
            
            # For original_data nested structure
            if 'original_data' in article_data:
                return self.is_article_already_processed(article_data['original_data'])
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking if article already processed: {e}")
            return False

    def load_existing_processed_articles(self) -> Dict[str, Any]:
        """Load already processed articles from rolling_articles.json to avoid reprocessing"""
        try:
            website_file = os.path.join(os.path.dirname(__file__), '..', 'Project-Better-French-Website', 'rolling_articles.json')
            if os.path.exists(website_file):
                with open(website_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    articles = data.get('articles', [])
                    
                    # Create lookup by URL and title
                    processed_lookup = {}
                    for article in articles:
                        # Index by original link
                        link = article.get('link') or article.get('original_article_link', '')
                        if link:
                            processed_lookup[link] = article
                        
                        # Index by title (normalized)
                        title = article.get('title') or article.get('original_article_title', '')
                        if title:
                            normalized_title = title.lower().strip()
                            processed_lookup[f"title:{normalized_title}"] = article
                    
                    logger.info(f"🔍 Loaded {len(processed_lookup)} processed articles for duplicate detection")
                    return processed_lookup
            
            return {}
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing processed articles: {e}")
            return {}

    def filter_already_processed_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out articles that have already been AI-processed"""
        if not self.ai_config.get('skip_duplicate_processing', True):
            logger.info("🔄 Duplicate processing check disabled in config")
            return articles
        
        # Load existing processed articles
        processed_lookup = self.load_existing_processed_articles()
        
        new_articles = []
        skipped_count = 0
        
        for article in articles:
            # Extract article data
            if 'original_data' in article:
                article_data = article['original_data']
                article_title = article_data.get('title', '')
                article_link = article_data.get('link', '')
            else:
                article_data = article
                article_title = article.get('title', '')
                article_link = article.get('link', '')
            
            # Check if already processed
            is_duplicate = False
            
            # Check by link
            if article_link and article_link in processed_lookup:
                is_duplicate = True
                logger.debug(f"🔄 Skipping already processed article (by link): {article_title[:50]}...")
            
            # Check by title
            elif article_title:
                normalized_title = article_title.lower().strip()
                title_key = f"title:{normalized_title}"
                if title_key in processed_lookup:
                    is_duplicate = True
                    logger.debug(f"🔄 Skipping already processed article (by title): {article_title[:50]}...")
            
            # Check internal AI flags
            elif self.is_article_already_processed(article_data):
                is_duplicate = True
                logger.debug(f"🔄 Skipping already AI-enhanced article: {article_title[:50]}...")
            
            if is_duplicate:
                skipped_count += 1
            else:
                new_articles.append(article)
        
        if skipped_count > 0:
            logger.info(f"💰 Saved API credits: Skipped {skipped_count} already-processed articles")
            logger.info(f"🔄 Processing {len(new_articles)} new articles (was {len(articles)})")
        else:
            logger.info(f"✅ All {len(articles)} articles are new - no duplicates found")
        
        return new_articles

    def batch_process_articles(self, articles: List[Dict[str, Any]]) -> List[ProcessedArticle]:
        """Process articles in cost-optimized batches"""
        logger.info(f"🤖 Starting batch AI processing of {len(articles)} articles...")
        
        # STEP 1: Filter out already processed articles to save API credits
        articles_to_process = self.filter_already_processed_articles(articles)
        
        if not articles_to_process:
            logger.info("✅ No new articles to process - all were already AI-enhanced")
            return []
        
        # Check cost limits
        can_process, limit_message = self.check_cost_limits()
        if not can_process:
            logger.warning(f"💰 {limit_message}")
            return []
        
        # Limit to max articles per day
        max_articles = self.cost_config['max_ai_articles_per_day']
        if len(articles_to_process) > max_articles:
            articles_to_process = articles_to_process[:max_articles]
            logger.info(f"📊 Processing top {max_articles} articles (limit applied)")
        
        processed_articles = []
        batch_start_time = time.time()
        
        # Process articles with rate limiting
        for i, article in enumerate(articles_to_process):
            # Check cost limits before each article
            can_continue, limit_message = self.check_cost_limits()
            if not can_continue:
                logger.warning(f"💰 Stopping batch processing: {limit_message}")
                break
            
            logger.info(f"🔄 Processing article {i+1}/{len(articles_to_process)}: {article.get('original_data', article).get('title', 'Unknown')[:50]}...")
            
            processed = self.process_single_article(article)
            if processed:
                processed_articles.append(processed)
            
            # Rate limiting delay
            if i < len(articles_to_process) - 1:  # Don't delay after last article
                time.sleep(self.ai_config['rate_limit_delay'])
        
        # Calculate batch statistics
        batch_duration = time.time() - batch_start_time
        success_count = len(processed_articles)
        failure_count = len(articles_to_process) - success_count
        success_rate = (success_count / len(articles_to_process)) * 100 if articles_to_process else 0
        
        # Update processing statistics
        self.processing_stats['articles_processed_today'] += success_count
        if batch_duration > 0:
            self.processing_stats['average_processing_time'] = batch_duration / len(articles_to_process)
        self.processing_stats['success_rate'] = success_rate
        
        # Log batch completion
        logger.info("🎉 Batch processing completed:")
        logger.info(f"   ✅ Successfully processed: {success_count}/{len(articles_to_process)} articles")
        logger.info(f"   💰 Total cost: ${self.daily_cost:.4f}")
        logger.info(f"   ⏱️ Batch duration: {batch_duration:.2f}s")
        logger.info(f"   📊 Success rate: {success_rate:.1f}%")
        
        if failure_count > 0:
            logger.warning(f"   ⚠️ Failed articles: {failure_count}")
        
        return processed_articles
    
    def save_processed_articles(self, processed_articles: List[ProcessedArticle], filename: str = None) -> str:
        """Save processed articles with metadata"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/live/ai_processed_articles_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Calculate statistics
        if processed_articles:
            scores = [a.quality_scores.get('total_score', 0) for a in processed_articles if a.quality_scores]
            avg_score = sum(scores) / len(scores) if scores else 0
        else:
            avg_score = 0
        
        data = {
            "metadata": {
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "total_processed": len(processed_articles),
                "ai_processor_version": "Cost-Optimized AI Processor 1.0",
                "automation_system": "Better French Max Automated System",
                "model_used": self.model,
                "processing_statistics": self.processing_stats,
                "cost_efficiency": {
                    "daily_cost": self.daily_cost,
                    "cost_per_article": self.daily_cost / len(processed_articles) if processed_articles else 0,
                    "api_calls_used": self.daily_api_calls,
                    "articles_per_call_ratio": len(processed_articles) / self.daily_api_calls if self.daily_api_calls else 0
                },
                "quality_metrics": {
                    "average_total_score": avg_score,
                    "articles_from_top_sources": len([a for a in processed_articles if a.source_name in ['Le Monde', 'Le Figaro', 'France Info']])
                }
            },
            "processed_articles": [asdict(article) for article in processed_articles]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 AI processed articles saved: {filename}")
        return filename
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary for monitoring"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "active" if self.daily_api_calls < self.cost_config['max_ai_calls_per_day'] else "limit_reached",
            "daily_statistics": self.processing_stats,
            "cost_tracking": {
                "daily_cost": self.daily_cost,
                "daily_budget": self.cost_config['daily_cost_limit'],
                "remaining_budget": max(0, self.cost_config['daily_cost_limit'] - self.daily_cost),
                "api_calls_used": self.daily_api_calls,
                "api_calls_limit": self.cost_config['max_ai_calls_per_day']
            },
            "efficiency_metrics": {
                "cost_per_article": self.daily_cost / max(1, self.processing_stats['articles_processed_today']),
                "average_processing_time": self.processing_stats['average_processing_time'],
                "success_rate": self.processing_stats['success_rate']
            }
        }
    
    def reset_daily_counters(self):
        """Reset daily tracking counters (called at midnight)"""
        self.daily_cost = 0.0
        self.daily_api_calls = 0
        self.processing_stats = {
            'articles_processed_today': 0,
            'total_cost_today': 0.0,
            'average_processing_time': 0.0,
            'success_rate': 100.0,
            'failed_articles': []
        }
        logger.info("🔄 Daily AI processing counters reset")

    # ------------------------------------------------------------------
    # Helper: more forgiving JSON extraction from LLM output
    # ------------------------------------------------------------------
    def _safe_json_loads(self, text: str):
        """Attempt to load JSON even if the model wrapped it with prose or code fences."""
        text = text.strip()

        # Strip ```json fences
        if text.startswith('```'):
            # keep after first newline following opening fence
            first_newline = text.find('\n')
            if first_newline != -1:
                text = text[first_newline+1:]
            if text.startswith('{') or text.startswith('['):
                pass
        if text.endswith('```'):
            text = text[:-3].rstrip()

        # If it still starts with prose, try to find first { or [
        first_curly = text.find('{')
        first_square = text.find('[')
        starts = [i for i in (first_curly, first_square) if i != -1]
        if starts:
            start = min(starts)
            if start > 0:
                text = text[start:]

        # Likewise trim any trailing prose after the last } or ]
        last_curly = text.rfind('}')
        last_square = text.rfind(']')
        ends = [i for i in (last_curly, last_square) if i != -1]
        if ends:
            end = max(ends) + 1
            text = text[:end]

        try:
            return json.loads(text)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Named-entity extraction using spaCy (PERSON / GPE / LOC)
    # ------------------------------------------------------------------
    def _spacy_entities(self, text: str) -> set[str]:
        if not text or _NLP_EN is None or _NLP_FR is None:
            return set()
        ents = []
        for nlp in (_NLP_EN, _NLP_FR):
            doc = nlp(text)
            ents.extend([span.text for span in doc.ents if span.label_ in ("PERSON", "GPE", "LOC")])
        return set(ents)

# Test function for development
def test_ai_processor():
    """Test the AI processor functionality"""
    print("🧪 Testing Cost-Optimized AI Processor...")
    
    # Check if API key is available
    if not os.getenv('OPENROUTER_API_KEY'):
        print("⚠️ No OpenRouter API key found - creating mock test")
        
        # Create processor anyway for testing structure
        processor = CostOptimizedAIProcessor()
        
        # Test article structure
        test_article = {
            'original_data': {
                'title': 'Test: Nouvelle réforme de l\'immigration en France',
                'summary': 'Le gouvernement annonce des changements importants.',
                'content': 'Le ministre a présenté les nouvelles mesures...',
                'source_name': 'Test Source',
                'link': 'https://example.com',
                'published': '2024-01-01T10:00:00Z'
            },
            'quality_score': 8.0,
            'relevance_score': 9.0,
            'importance_score': 8.5,
            'total_score': 25.5,
            'curation_id': 'test-123'
        }
        
        print(f"🎯 Test article created with score: {test_article['total_score']}")
        print(f"💰 Daily cost limit: ${processor.cost_config['daily_cost_limit']}")
        print(f"📄 Max articles per day: {processor.cost_config['max_ai_articles_per_day']}")
        
        # Test cost limits
        can_process, message = processor.check_cost_limits()
        print(f"🚦 Cost check: {can_process} - {message}")
        
        # Get processing summary
        summary = processor.get_processing_summary()
        print(f"📊 Processing status: {summary['status']}")
        
        print("✅ AI Processor structure test completed (no API calls made)")
        return
    
    # Full test with API if key is available
    processor = CostOptimizedAIProcessor()
    
    # Create test article
    test_article = {
        'original_data': {
            'title': 'Nouvelle loi sur l\'immigration: ce qui va changer pour les étudiants étrangers',
            'summary': 'Le Parlement a adopté une nouvelle loi qui modifie les conditions de séjour pour les étudiants étrangers en France.',
            'content': 'La nouvelle législation, votée hier soir, prévoit des changements significatifs dans les procédures d\'obtention et de renouvellement des titres de séjour pour les étudiants internationaux.',
            'source_name': 'Le Monde',
            'link': 'https://example.com/test-article',
            'published': '2024-01-01T10:00:00Z'
        },
        'quality_score': 8.5,
        'relevance_score': 9.2,
        'importance_score': 8.8,
        'total_score': 26.5,
        'curation_id': 'test-456',
        'curated_at': '2024-01-01T10:00:00Z'
    }
    
    print(f"🎯 Test article: {test_article['original_data']['title'][:50]}...")
    print(f"📊 Quality score: {test_article['total_score']}/30")
    
    # Test single article processing
    try:
        processed = processor.process_single_article(test_article)
        if processed:
            print(f"✅ AI processing successful:")
            print(f"   🇫🇷 French title: {processed.simplified_french_title}")
            print(f"   🇬🇧 English title: {processed.simplified_english_title}")
            print(f"   💰 Cost: ${processed.processing_cost:.4f}")
        else:
            print("❌ AI processing failed")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    # Test batch processing (with single article)
    try:
        batch_result = processor.batch_process_articles([test_article])
        print(f"📦 Batch processing result: {len(batch_result)} articles processed")
        
        if batch_result:
            # Save results
            saved_file = processor.save_processed_articles(batch_result)
            print(f"💾 Results saved: {saved_file}")
    except Exception as e:
        print(f"❌ Batch test error: {e}")
    
    # Get summary
    summary = processor.get_processing_summary()
    print(f"📈 Final summary: {summary['daily_statistics']['articles_processed_today']} articles, ${summary['cost_tracking']['daily_cost']:.4f} cost")
    
    print("✅ AI Processor test completed")

if __name__ == "__main__":
    test_ai_processor() 