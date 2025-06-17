"""Config values for AI-Engine v2 stand-alone pipeline.
You can tweak weights or sources here without touching code.
"""
from __future__ import annotations

SOURCES = [
    {
        "name": "Le Monde",
        "rss": "https://www.lemonde.fr/rss/en_continu.xml",
        "category": "general",
    },
    {
        "name": "France 24",
        "rss": "https://www.france24.com/fr/rss",
        "category": "general",
    },
    # Add or remove sources freely
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
]

MEDIUM_RELEVANCE_KEYWORDS = [
    "retraite", "impôts", "URSSAF", "CAF", "énergie", "inflation", "prix", "taxe foncière",
]

CURATOR_WEIGHTS = {
    "relevance": 1.2,
    "practical": 1.0,
    "newsworthiness": 0.8,
} 