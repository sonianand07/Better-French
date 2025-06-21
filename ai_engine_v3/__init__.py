"""AI-Engine v2 package.

Modular, test-driven rewrite of the legacy AI-Engine.

# Better French AI-Engine v3
# ---------------------------------
# This package is a copy of v2 but will evolve towards:
#   • two-stage pipeline (fetch + qualify)
#   • LLM-based relevance scoring
#   • daily 50-article cap per profile
"""

__all__ = [
    "models",
    "client",
    "storage",
    "processor",
    "validator",
] 