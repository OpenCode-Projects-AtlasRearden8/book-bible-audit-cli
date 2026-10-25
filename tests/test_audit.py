from __future__ import annotations

from bookbible.bible import Bible, Entry
from bookbible.manuscript import load_text
from bookbible.audit import audit

ELINA = dict(
    category="character",
    name="Elena Vance",
    aliases=["Lena"],
    eye_color="green",
    title="Captain",
    first_seen="Day 3",
    died="Day 5",
    status="dead",
)


def kinds(result):
    return {f.kind for f in result.findings}


def test_sample_finds_eye_color_contradiction(valid_audit):
    matches = [f for f in valid_audit.findings if f.kind == "eye-color"]
    assert matches, "expected at least one eye-color contradiction"
    assert any("Marta Halloran" in f.message for f in matches)


def test_sample_finds_timeline_contradiction(valid_audit):
    matches = [f for f in valid_audit.findings if f.kind == "timeline"]
    assert matches
    assert any("Day 2" in f.message for f in matches)


def test_sample_finds_dead_name_after_death(valid_audit):
    matches = [f for f in valid_audit.findings if f.kind == "dead-name" and f.severity == "high"]
    assert matches
    assert any("Day 6" in f.message for f in matches)


def test_sample_finds_title_mismatch(valid_audit):
    matches = [f for f in valid_audit.findings if f.kind == "title" and f.severity == "high"]
    assert any("Doctor" in f.message for f in matches)


def test_sample_finds_unused_entity(valid_audit):
    matches = [f for f in valid_audit.findings if f.kind == "unused-entity"]
    assert any("Ravenreach" in f.message for f in matches)


def test_sample_finds_repeated_phrase(valid_audit):
    phrases = [r["phrase"] for r in valid_audit.repeats]
    assert any("lighthouse" in p for p in phrases)


def test_agreeing_eye_color_is_silent():
    bible = Bible(entries=[Entry(**{**ELINA, "eye_color": "grey"})])
    text = "Elena's eyes were grey."
    result = audit(bible, text)
    assert not [f for f in result.findings if f.kind == "eye-color"]


def test_matching_title_is_silent():
    bible = Bible(entries=[Entry(**ELINA)])
    result = audit(bible, "Captain Elena Vance took the deck.")
    assert not [f for f in result.findings if f.kind == "title"]


def test_title_without_bible_entry_is_medium():
    entry = Entry(category="character", name="Kell", eye_color="", title="")
    bible = Bible(entries=[entry])
    result = audit(bible, "Sergeant Kell carried the rope.")
    titles = [f for f in result.findings if f.kind == "title"]
    assert len(titles) == 1 and titles[0].severity == "medium"


def test_dead_before_death_not_flagged():
    bible = Bible(entries=[Entry(**ELINA)])
    result = audit(bible, "On Day 2, Elena sharpened her blade.")
    assert not [f for f in result.findings if f.kind == "dead-name" and f.severity == "high"]


def test_dead_name_mention_info_finding():
    bible = Bible(entries=[Entry(**ELINA)])
    result = audit(bible, "Elena smiled down the hallway.")
    kinds_present = kinds(result)
    assert "dead-name" in kinds_present


def test_unused_entities_flagged():
    bible = Bible(
        entries=[Entry(category="character", name="Zora"), Entry(category="place", name="Riva")]
    )
    result = audit(bible, "Kell waited near the wall.")
    unused = [f for f in result.findings if f.kind == "unused-entity"]
    assert {f.entity for f in unused} == {"Zora", "Riva"}


def test_repeated_phrase_threshold():
    bible = Bible(entries=[Entry(category="place", name="Millhaven")])
    text = " ".join(["the old lighthouse keeper watched"] * 3)
    result = audit(bible, text, repeat_threshold=3)
    assert result.repeats
    quiet = audit(bible, text, repeat_threshold=90)
    assert quiet.repeats == []


def test_counts_by_severity(valid_audit):
    counts = valid_audit.counts_by_severity()
    assert counts["high"] >= 1
    assert sum(counts.values()) == len(valid_audit.findings)


def test_notes_collected(bible, manuscript_path):
    text = load_text(str(manuscript_path))
    result = audit(bible, text)
    note_names = {n["name"] for n in result.notes}
    assert "Elena Vance" in note_names
    assert "Millhaven" in note_names
