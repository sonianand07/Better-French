from ai_engine_v2.validator import validate_titles_payload, validate_explanations_payload


def test_validate_titles_success():
    raw = '{"simplified_french_title": "Titre", "simplified_english_title": "Title", "french_summary": "Résumé", "english_summary": "Summary", "difficulty":"B1", "tone":"neutral"}'
    ok, data, reason = validate_titles_payload(raw)
    assert ok is True
    assert data["simplified_french_title"] == "Titre"


def test_validate_titles_missing_key():
    raw = '{"simplified_french_title": "Titre"}'
    ok, _data, reason = validate_titles_payload(raw)
    assert ok is False


def test_validate_explanations_success():
    raw = '[{"original_word": "mot", "display_format": "**mot**", "explanation": "word"}]'
    ok, data, _ = validate_explanations_payload(raw)
    assert ok is True
    assert isinstance(data, list)


def test_validate_explanations_error():
    raw = '{"foo": "bar"}'
    ok, _data, _ = validate_explanations_payload(raw)
    assert ok is False


def test_invalid_cefr():
    raw = '{"simplified_french_title": "Titre", "simplified_english_title": "Title", "french_summary": "Résumé", "english_summary": "Summary", "difficulty":"Z1", "tone":"neutral"}'
    ok, _data, _ = validate_titles_payload(raw)
    assert ok is False


def test_invalid_tone():
    raw = '{"simplified_french_title": "Titre", "simplified_english_title": "Title", "french_summary": "Résumé", "english_summary": "Summary", "difficulty":"B1", "tone":"angry"}'
    ok, _data, _ = validate_titles_payload(raw)
    assert ok is False 