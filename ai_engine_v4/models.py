from __future__ import annotations

from typing import Optional

from pydantic import Field

# Import base Article model from v3 to inherit every existing field & validators
from ai_engine_v3.models import Article as _BaseArticle  # type: ignore


class Article(_BaseArticle):  # noqa: D101 – inherit docstring
    quality_checked: bool = Field(False, description="Has the high-tier verifier reviewed & fixed this article?")

    class Config(_BaseArticle.Config):  # type: ignore
        title = "ArticleV4" 