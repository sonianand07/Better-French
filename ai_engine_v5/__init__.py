"""
AI Engine v5: Intelligent Separated Architecture

The next evolution in Better French news curation:
- Semantic deduplication (no more heat wave spam!)
- Topic-aware selection (balanced content)
- Separated workflows (collection vs processing)
- Website-aware curation (considers existing content)

Key Innovation: Solves repetitive content through intelligent semantic understanding.
"""

__version__ = "5.0.0"
__author__ = "Better French Team"

# Core components
from .core.curator.intelligent_curator import IntelligentCurator, Article, CurationResult

__all__ = [
    "IntelligentCurator",
    "Article", 
    "CurationResult",
] 