from __future__ import annotations

from bookbible.manuscript import load_text, normalize, split_sentences


def test_split_sentences_sample(manuscript_path):
    text = load_text(str(manuscript_path))
    sentences = split_sentences(text)
    assert len(sentences) > 3
    assert any("Marta Halloran" in s for s in sentences)


def test_split_sentences_empty():
    assert split_sentences("") == []
    assert split_sentences("   \n  ") == []


def test_normalize_strips_honorific_periods():
    assert normalize("Dr. Halloran said.") == "Dr Halloran said."


def test_load_text_is_utf8(sample_csv_bible_path):
    text = load_text(str(sample_csv_bible_path))
    assert "Elena Vance" in text
