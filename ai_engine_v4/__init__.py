"""AI-Engine v4 – verification pipeline.

This package extends v3 functionality by adding a high-tier verification
step that achieves full tooltip coverage and QA of simplified titles &
summaries.
"""

from importlib import metadata as _md

__version__ = "0.1.0"

# Re-export primary helpers so callers can simply `from ai_engine_v4 import Article, Storage`
from .models import Article  # noqa: F401
from .storage import Storage  # noqa: F401 