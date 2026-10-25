"""Load and normalize a series bible from CSV or JSON."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = {"character", "place"}

CSV_COLUMNS = [
    "category",
    "name",
    "aliases",
    "eye_color",
    "title",
    "first_seen",
    "died",
    "status",
    "notes",
]


@dataclass
class Entry:
    category: str
    name: str
    aliases: list[str] = field(default_factory=list)
    eye_color: str = ""
    title: str = ""
    first_seen: str = ""
    died: str = ""
    status: str = ""
    notes: str = ""

    @property
    def all_names(self) -> list[str]:
        return [self.name] + list(self.aliases)


@dataclass
class Bible:
    entries: list[Entry] = field(default_factory=list)

    @property
    def characters(self) -> list[Entry]:
        return [e for e in self.entries if e.category == "character"]

    @property
    def places(self) -> list[Entry]:
        return [e for e in self.entries if e.category == "place"]

    def find_canonical(self, surface: str) -> Entry | None:
        surface = surface.strip().rstrip("'\"").lower()
        for entry in self.entries:
            for name in entry.all_names:
                if name.strip().lower() == surface:
                    return entry
        return None


def _clean(value: str) -> str:
    return (value or "").strip()


def _split_aliases(value: str) -> list[str]:
    return [v.strip() for v in (value or "").replace(";", ",").split(",") if v.strip()]


def _norm_category(value: str) -> str:
    value = _clean(value).lower()
    if value in ("characters", "person", "people"):
        return "character"
    if value in ("locations", "location", "places", "setting"):
        return "place"
    return value


def _entry_from_row(row: dict[str, str], notes: str = "") -> Entry:
    return Entry(
        category=_norm_category(row.get("category", "")),
        name=_clean(row.get("name", "")),
        aliases=_split_aliases(row.get("aliases", "")),
        eye_color=_clean(row.get("eye_color", "")),
        title=_clean(row.get("title", "")),
        first_seen=_clean(row.get("first_seen", "")),
        died=_clean(row.get("died", "")),
        status=_norm_status(_clean(row.get("status", ""))),
        notes=notes or _clean(row.get("notes", "")),
    )


def _norm_status(value: str) -> str:
    value = value.lower()
    if value in ("dead", "deceased", "killed", "deceased.", "dies"):
        return "dead"
    if value in ("alive", "living"):
        return "alive"
    return value


def parse_csv(path: str | Path) -> Bible:
    bible = Bible()
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
        if "name" not in fieldnames:
            raise ValueError(f"CSV bible must have a 'name' column: {path}")
        for row in reader:
            normalized = {
                (key or "").strip().lower(): row.get(key) or "" for key in row
            }
            entry = _entry_from_row(normalized)
            if entry.name:
                bible.entries.append(entry)
    return bible


def _parse_json_bible(data: dict) -> Bible:
    bible = Bible()
    for group, category in (("characters", "character"), ("places", "place")):
        for item in data.get(group, []):
            if not isinstance(item, dict):
                continue
            entry = Entry(
                category=category,
                name=_clean(str(item.get("name", ""))),
                aliases=_split_aliases(str(item.get("aliases", ""))),
                eye_color=_clean(str(item.get("eye_color", ""))),
                title=_clean(str(item.get("title", ""))),
                first_seen=_clean(str(item.get("first_seen", ""))),
                died=_clean(str(item.get("died", ""))),
                status=_norm_status(_clean(str(item.get("status", "")))),
                notes=_clean(str(item.get("notes", ""))),
            )
            if entry.name:
                bible.entries.append(entry)
    return bible


def parse_json(path: str | Path) -> Bible:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON bible must be an object of characters/places: {path}")
    bible = _parse_json_bible(data)
    if not bible.entries:
        raise ValueError(f"JSON bible has no characters or places: {path}")
    return bible


def parse_bible(path: str | Path) -> Bible:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_csv(path)
    if suffix == ".json":
        return parse_json(path)
    raise ValueError(f"Unsupported bible format '{suffix}' (use .csv or .json): {path}")
