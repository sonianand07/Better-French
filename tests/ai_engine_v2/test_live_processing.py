import os
import pytest
from ai_engine_v2.models import Article, QualityScores
from ai_engine_v2.processor import ProcessorV2


@pytest.mark.skipif("OPENROUTER_API_KEY" not in os.environ, reason="requires OpenRouter key")
def test_live_processing_single_article():
    qs = QualityScores(quality_score=8, relevance_score=8, importance_score=7, total_score=23)
    art = Article(
        original_article_title="Inflation : les prix alimentaires vont-ils enfin baisser ?",
        original_article_link="https://example.com/article",
        original_article_published_date="2025-06-16",
        source_name="TestSource",
        quality_scores=qs,
    )
    proc = ProcessorV2()
    out = proc.process_article(art)
    assert out.display_ready is True
    assert out.simplified_french_title
    assert out.contextual_title_explanations 