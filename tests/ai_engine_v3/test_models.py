from ai_engine_v3.models import Article, QualityScores

def test_display_ready_flag_v3():
    qs = QualityScores(quality_score=9, relevance_score=8, importance_score=7, total_score=24)
    art = Article(
        original_article_title="Titre original",
        original_article_link="https://example.com/story",
        original_article_published_date="2025-06-16",
        source_name="Le Monde",
        quality_scores=qs,
        simplified_french_title="Titre simplifié",
        simplified_english_title="Simplified title",
        contextual_title_explanations=[
            {
                "original_word": "Titre",
                "display_format": "**Titre:** Title",
                "explanation": "The heading",
                "cultural_note": ""
            }
        ],
    )
    assert art.display_ready is True 