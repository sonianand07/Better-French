from ai_engine_v3.validator import validate_titles_payload, validate_explanations_payload


def test_validate_titles_success():
    raw = '{"simplified_french_title": "Titre", "simplified_english_title": "Title", "french_summary": "Résumé", "english_summary": "Summary", "difficulty":"B1", "tone":"neutral"}'
    ok, data, _ = validate_titles_payload(raw)
    assert ok is True
    assert data["simplified_french_title"] == "Titre"


def test_validate_explanations_success():
    raw = '[{"original_word": "mot", "display_format": "**Word:** mot", "explanation": "A basic unit of language", "cultural_note": "Commonly used example word in French textbooks."}]'
    ok, data, _ = validate_explanations_payload(raw)
    assert ok is True and isinstance(data, list) 