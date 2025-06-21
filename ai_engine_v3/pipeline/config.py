"""Config values for AI-Engine v2 stand-alone pipeline.
You can tweak weights or sources here without touching code.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# RSS / Atom feeds scraped by v3 Fetcher
# ---------------------------------------------------------------------------
SOURCES = [
    # General major papers
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.lefigaro.fr/rss/figaro_actualites.xml",
    "https://www.lesechos.fr/rss/rss_la_une.xml",
    "https://www.liberation.fr/arc/outboundfeeds/rss_all/",

    # Broadcast / agencies
    "https://www.france24.com/fr/rss",
    "https://www.francetvinfo.fr/titres.rss",
    "https://www.rfi.fr/fr/podcasts/podcasts",
    "https://www.afp.com/en/rss/afp-news?format=xml",  # AFP English general

    # Magazines / analysis
    "https://www.nouvelobs.com/rss.xml",
]

SCORING_WEIGHTS = {
    "relevance": 1.2,
    "practical_impact": 1.0,
    "newsworthiness": 0.8,
}

FAST_TRACK_THRESHOLDS = {
    "relevance": 8.0,
    "practical_impact": 7.0,
}

# ---------------- Curator v2 keyword banks ----------------
HIGH_RELEVANCE_KEYWORDS = [
    # Visas & immigration
    "visa", "titre de séjour", "carte de séjour", "naturalisation", "immigration", "étranger",
    # Work & salary
    "smic", "salaire", "cotisations", "travail", "code du travail", "congé", "prélèvement à la source",
    # Housing & cost of living
    "loyer", "caf", "APL", "logement", "bail", "pouvoir d'achat",
    # Transport strikes / SNCF / RATP
    "grève", "SNCF", "RATP", "trafic", "panne",
    # Health & social security
    "sécurité sociale", "ameli", "mutuelle", "assurance maladie",
    # --- Added June 20 2025 ---------------------------------------
    # Civic & daily-life topics that matter to any resident of France
    "france", "politique", "économie", "justice", "santé", "écologie",
    # Day-to-day admin & services
    "assurance habitation", "ram", "carte vitale", "taxe d'habitation",
    "mutuelle étudiante", "doctolib", "carte navigo",
]

MEDIUM_RELEVANCE_KEYWORDS = [
    "retraite", "impôts", "URSSAF", "CAF", "énergie", "inflation", "prix", "taxe foncière",
    # --- Added June 20 2025 ---------------------------------------
    "olympiques", "jeux olympiques", "élections", "météo", "météo-extrême",
    "grève nationale", "canicule", "tempête", "sécheresse",
]

CURATOR_WEIGHTS = {
    "relevance": 1.2,
    "practical": 1.0,
    "newsworthiness": 0.8,
} 