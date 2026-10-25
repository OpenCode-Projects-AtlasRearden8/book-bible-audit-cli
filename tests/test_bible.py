from __future__ import annotations

import pytest

from bookbible.bible import Entry, parse_bible


def test_parse_csv_sample(sample_csv_bible_path):
    bible = parse_bible(sample_csv_bible_path)
    names = {entry.name for entry in bible.entries}
    assert {"Elena Vance", "Marta Halloran", "Kell"} <= names
    characters = bible.characters
    assert len(characters) == 3
    assert len(bible.places) == 2


def test_parse_csv_aliases_and_attributes(sample_csv_bible_path):
    bible = parse_bible(sample_csv_bible_path)
    elena = bible.find_canonical("Elena Vance")
    assert elena is not None
    assert elena.aliases == ["Lena"]
    assert elena.eye_color == "green"
    assert elena.title == "Captain"
    assert elena.status == "dead"


def test_parse_json_matches_csv(sample_csv_bible_path, sample_json_bible_path):
    csv_bible = parse_bible(sample_csv_bible_path)
    json_bible = parse_bible(sample_json_bible_path)
    assert [(e.category, e.name, e.eye_color, e.title) for e in csv_bible.entries] == [
        (e.category, e.name, e.eye_color, e.title) for e in json_bible.entries
    ]


def test_find_canonical_aliases():
    entries = [
        Entry(category="character", name="Ada Quinn", aliases=["Q"]),
    ]
    from bookbible.bible import Bible

    book = Bible(entries=entries)
    assert book.find_canonical("ada quinn").name == "Ada Quinn"
    assert book.find_canonical("q").name == "Ada Quinn"
    assert book.find_canonical("Nobody") is None


def test_unsupported_suffix(tmp_path):
    path = tmp_path / "bible.yaml"
    path.write_text("name: x")
    with pytest.raises(ValueError):
        parse_bible(path)


def test_csv_without_name_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("thing,place\n,Rome\n")
    with pytest.raises(ValueError):
        parse_bible(path)


def test_json_without_entries(tmp_path):
    import json

    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"characters": [], "places": []}))
    with pytest.raises(ValueError):
        parse_bible(path)
