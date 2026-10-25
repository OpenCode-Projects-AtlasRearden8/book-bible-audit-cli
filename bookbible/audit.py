"""Run all manuscript audits against the series bible."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .manuscript import split_sentences
from .names import find_mentions, name_re
from .timeline import parse_ref, refs_in_sentence

COLORS = {
    "amber", "black", "blue", "brown", "gold", "gray", "green", "grey",
    "hazel", "ice blue", "red", "silver", "violet",
}

COLOR_RE = re.compile(
    r"\b(?:dark\s+)?(?:" + "|".join(sorted(COLORS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

EYE_WINDOW_RE = re.compile(r".{0,70}(?:^|\s)eyes?(?:\s|$).{0,70}", re.IGNORECASE)

TITLES = {
    "admiral", "baron", "captain", "chief", "coach", "colonel", "commander",
    "count", "countess", "dame", "doctor", "dr", "duke", "father", "general",
    "king", "lady", "lieutenant", "lord", "major", "master", "miss", "mister",
    "mother", "mr", "mrs", "ms", "nurse", "professor", "queen", "sarge",
    "sergeant", "sir",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z-]*")

_TITLE_SYNONYMS = {"dr": "doctor", "mr": "mister", "mrs": "missus", "sarge": "sergeant"}

REPEAT_N = 3
MIN_TOKEN_LEN = 3

STOPWORDS = {
    "the", "and", "a", "an", "of", "to", "in", "it", "was", "that", "her",
    "his", "with", "on", "at", "had", "he", "she", "they", "but", "for",
    "as", "not", "so", "then", "said", "him", "them", "its", "their",
    "into", "out", "off", "over", "under", "again", "there", "here",
    "when", "while", "than", "this", "these", "those", "too", "very",
}


@dataclass
class Finding:
    kind: str
    severity: str
    entity: str
    message: str
    detail: str = ""


@dataclass
class AuditResult:
    entities: list[dict] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    repeats: list[dict] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    sentence_count: int = 0

    def counts_by_severity(self) -> dict[str, int]:
        counts = {"high": 0, "medium": 0, "info": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts


def _norm(value: str) -> str:
    return value.strip().lower().replace("-", " ").replace("grey", "gray")


def _color_agrees(bible_color: str, text_color: str) -> bool:
    a, b = _norm(bible_color), _norm(text_color)
    return a in b or b in a


def check_eye_color(entry, sentence: str) -> Finding | None:
    if not entry.eye_color:
        return None
    pattern = name_re(entry)
    for window in EYE_WINDOW_RE.finditer(sentence):
        text = window.group(0)
        if not pattern.search(text):
            continue
        color_match = COLOR_RE.search(text)
        if not color_match:
            continue
        detected = color_match.group(0)
        if not _color_agrees(entry.eye_color, detected):
            return Finding(
                kind="eye-color",
                severity="high",
                entity=entry.name,
                message=(
                    f"Bible says {entry.name}'s eyes are '{entry.eye_color}' "
                    f"but the text describes them as '{detected}'."
                ),
                detail=text.strip(),
            )
        return None
    return None


def _norm_title(word: str) -> str:
    parts = word.split()
    last = parts[-1].rstrip(".").lower() if parts else ""
    return _TITLE_SYNONYMS.get(last, last)


def check_title(entry, sentence: str) -> list[Finding]:
    canonical = _norm_title(entry.title)
    findings: list[Finding] = []
    for match in name_re(entry).finditer(sentence):
        prefix_tokens = [
            (m.group(0), m.start(), m.end())
            for m in TOKEN_RE.finditer(sentence[: match.start()])
        ]
        suffix = re.match(
            r"\s*,\s*the\s+(?P<title>[A-Za-z][A-Za-z-]*)",
            sentence[match.end():],
        )
        seen_titles = []
        if prefix_tokens and _norm_title(prefix_tokens[-1][0]) in TITLES:
            seen_titles.append(_norm_title(prefix_tokens[-1][0]))
        if suffix:
            used = _norm_title(suffix.group("title"))
            if used in TITLES:
                seen_titles.append(used)
        for used in seen_titles:
            if canonical and used != canonical:
                findings.append(
                    Finding(
                        kind="title",
                        severity="high",
                        entity=entry.name,
                        message=(
                            f"Bible titles {entry.name} as '{entry.title}' "
                            f"but the text calls them '{used.title()}'."
                        ),
                        detail=sentence,
                    )
                )
            elif not canonical:
                findings.append(
                    Finding(
                        kind="title",
                        severity="medium",
                        entity=entry.name,
                        message=(
                            f"Text uses the title '{used.title()}' for {entry.name}, "
                            "but the bible lists no title."
                        ),
                        detail=sentence,
                    )
                )
    return findings


def check_timeline(entry, sentence: str) -> list[Finding]:
    findings: list[Finding] = []
    first = parse_ref(entry.first_seen)
    died = parse_ref(entry.died)
    for ref in refs_in_sentence(sentence):
        if first and ref.kind == first.kind and ref.start < first.start:
            findings.append(
                Finding(
                    kind="timeline",
                    severity="high",
                    entity=entry.name,
                    message=(
                        f"Bible says {entry.name} first appears {entry.first_seen}, "
                        f"but the text places them at {ref.kind.title()} {ref.start}."
                    ),
                    detail=sentence,
                )
            )
        if died and ref.kind == died.kind and ref.start > died.start:
            findings.append(
                Finding(
                    kind="dead-name",
                    severity="high",
                    entity=entry.name,
                    message=(
                        f"Bible says {entry.name} died {entry.died}, but the text "
                        f"mentions them at {ref.kind.title()} {ref.start}."
                    ),
                    detail=sentence,
                )
            )
    return findings


def is_dead(entry) -> bool:
    return entry.status == "dead" or bool(entry.died)


def repeated_phrases(sentences: list[str], threshold: int = 3) -> list[dict]:
    counts: Counter[str] = Counter()
    for sentence in sentences:
        tokens = [word.lower() for word in TOKEN_RE.findall(sentence)]
        for index in range(len(tokens) - REPEAT_N + 1):
            gram = tokens[index: index + REPEAT_N]
            if any(len(w) < MIN_TOKEN_LEN or w in STOPWORDS for w in gram):
                continue
            counts[" ".join(gram)] += 1
    ranked = sorted(
        ((phrase, count) for phrase, count in counts.items() if count >= threshold),
        key=lambda item: (-item[1], item[0]),
    )
    return [{"phrase": phrase, "count": count} for phrase, count in ranked]


def collect_notes(bible) -> list[dict]:
    return [
        {"name": entry.name, "category": entry.category, "notes": entry.notes}
        for entry in bible.entries
        if entry.notes
    ]


def audit(bible, text: str, repeat_threshold: int = 3) -> AuditResult:
    sentences = split_sentences(text)
    result = AuditResult(sentence_count=len(sentences))

    by_name: dict[str, list] = defaultdict(list)
    for hit in find_mentions(bible, sentences):
        by_name[hit.entry.name].append(hit)

    seen: set[tuple] = set()

    def add(finding: Finding) -> None:
        key = (finding.kind, finding.entity, finding.message)
        if key not in seen:
            seen.add(key)
            result.findings.append(finding)

    for entry in bible.entries:
        hits = by_name.get(entry.name, [])
        result.entities.append(
            {
                "category": entry.category,
                "name": entry.name,
                "mentions": len(hits),
                "eye_color": entry.eye_color,
                "title": entry.title,
                "first_seen": entry.first_seen,
                "died": entry.died,
                "status": entry.status,
            }
        )
        for hit in hits:
            finding = check_eye_color(entry, hit.sentence)
            if finding:
                add(finding)
            for title_finding in check_title(entry, hit.sentence):
                add(title_finding)
            for timeline_finding in check_timeline(entry, hit.sentence):
                add(timeline_finding)
        if not hits:
            add(
                Finding(
                    kind="unused-entity",
                    severity="info",
                    entity=entry.name,
                    message=(
                        f"'{entry.name}' ({entry.category}) never appears in the manuscript."
                    ),
                )
            )
        elif entry.category == "character" and is_dead(entry):
            add(
                Finding(
                    kind="dead-name",
                    severity="info",
                    entity=entry.name,
                    message=(
                        f"'{entry.name}' is dead in the bible but appears {len(hits)} "
                        "time(s); confirm these are intentional flashbacks or after-life scenes."
                    ),
                )
            )

    result.repeats = repeated_phrases(sentences, repeat_threshold)
    result.notes = collect_notes(bible)
    return result
