"""Match bible names (canonical + aliases) inside manuscript sentences."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Hit:
    entry: object
    index: int
    sentence: str


GENERIC_SURFACE = {
    "fort", "mill", "port", "hall", "hill", "lake", "river", "town", "city",
    "square", "court", "bridge", "gate", "haven", "house", "manor",
}

TOKENIZE_RE = re.compile(r"[A-Za-z][A-Za-z-]+")


def _surface_forms(entry) -> list[str]:
    forms = {entry.name}
    forms.update(entry.aliases)
    tokens = TOKENIZE_RE.findall(entry.name)
    if len(tokens) > 1:
        for token in tokens:
            if len(token) >= 4 and token.lower() not in GENERIC_SURFACE:
                forms.add(token)
    return sorted((f for f in forms if f.strip()), key=len, reverse=True)


def name_re(entry) -> re.Pattern:
    alt = "|".join(re.escape(s) for s in _surface_forms(entry))
    return re.compile(r"\b(?:" + alt + r")\b", re.IGNORECASE)


def name_matches(entry, text: str) -> bool:
    return bool(name_re(entry).search(text))


def find_mentions(bible, sentences: list[str]) -> list[Hit]:
    hits = []
    for index, sentence in enumerate(sentences):
        for entry in bible.entries:
            if name_matches(entry, sentence):
                hits.append(Hit(entry, index, sentence))
    return hits
