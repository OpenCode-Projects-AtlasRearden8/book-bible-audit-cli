"""Split manuscript text into sentences and strip clutter."""

from __future__ import annotations

import re

SENTENCE_RE = re.compile(r"[^.!?]+[.!?]")
HONORIFIC_RE = re.compile(r"\b(Dr|Mr|Mrs|Ms|St|Prof|Gen|Col|Capt|Lt|Sgt)\.\s+")


def normalize(text: str) -> str:
    return HONORIFIC_RE.sub(r"\1 ", text)


def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    clean = normalize(text.replace("\r\n", " ").replace("\n", " "))
    parts = SENTENCE_RE.findall(clean)
    consumed = "".join(parts)
    tail = clean[len(consumed):].strip()
    sentences = [p.strip() for p in parts if p.strip()]
    if tail:
        sentences.append(tail)
    return sentences


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()
