"""Reference numbers like "Day 3" or "Chapter 7" extracted from a sentence."""

from __future__ import annotations

import re
from dataclasses import dataclass

REF_RE = re.compile(
    r"\b(?P<kind>chapter|ch|day)\s*\.?\s+(?P<num>\d+(?:-\d+)?)\b", re.IGNORECASE
)
YEAR_RE = re.compile(r"\b(?:in|by|during)\s+(?P<num>\d{4})\b", re.IGNORECASE)


@dataclass
class Ref:
    kind: str
    start: int


def parse_ref(value: str) -> Ref | None:
    match = REF_RE.search(value)
    if not match:
        return None
    kind = match.group("kind").lower().rstrip(".")
    if kind == "ch":
        kind = "chapter"
    return Ref(kind, int(match.group("num").split("-")[0]))


def refs_in_sentence(sentence: str) -> list[Ref]:
    refs = []
    for match in REF_RE.finditer(sentence):
        kind = match.group("kind").lower().rstrip(".")
        if kind == "ch":
            kind = "chapter"
        refs.append(Ref(kind, int(match.group("num").split("-")[0])))
    for match in YEAR_RE.finditer(sentence):
        refs.append(Ref("year", int(match.group("num"))))
    return refs
