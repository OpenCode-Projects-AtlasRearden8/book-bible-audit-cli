from __future__ import annotations

from bookbible.bible import Bible, Entry
from bookbible.names import find_mentions, name_matches


def make_entry(**kwargs) -> Entry:
    defaults = dict(category="character", name="Elena Vance", aliases=["Lena"])
    defaults.update(kwargs)
    return Entry(**defaults)


def test_full_name_matches():
    entry = make_entry()
    assert name_matches(entry, "Captain Elena Vance arrived at Millhaven.")


def test_first_token_matches_multiword_name():
    entry = make_entry()
    assert name_matches(entry, "Elena met the doctor at the sea wall.")


def test_alias_matches():
    entry = make_entry()
    assert name_matches(entry, "Lena nodded once.")


def test_possessive_matches():
    entry = make_entry()
    assert name_matches(entry, "Elena's eyes were grey.")
    assert name_matches(entry, "Vance's boat was gone.")


def test_no_partial_word_collisions():
    entry = make_entry(aliases=["Eli"])
    assert not name_matches(entry, "She was eligible for the post.")
    assert not name_matches(entry, "Selena waited by the gate.")


def test_generic_place_tokens_not_exposed():
    entry = Entry(category="place", name="Fort Alden")
    assert not name_matches(entry, "the old fort below the ridge")


def test_find_mentions_groups_by_sentence():
    bible = Bible(entries=[make_entry(), Entry(category="place", name="Millhaven")])
    sentences = ["Elena arrived at Millhaven.", "Nobody spoke.", "Elena left."]
    hits = find_mentions(bible, sentences)
    assert {h.index for h in hits} == {0, 2}
