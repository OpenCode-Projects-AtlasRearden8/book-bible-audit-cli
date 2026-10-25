from __future__ import annotations

from pathlib import Path

import pytest

from bookbible.audit import audit
from bookbible.bible import parse_bible

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def manuscript_path() -> Path:
    return ROOT / "samples" / "manuscript.md"


@pytest.fixture(scope="session")
def sample_csv_bible_path() -> Path:
    return ROOT / "samples" / "bible.csv"


@pytest.fixture(scope="session")
def sample_json_bible_path() -> Path:
    return ROOT / "samples" / "bible.json"


@pytest.fixture(scope="session")
def bible(sample_csv_bible_path):
    return parse_bible(sample_csv_bible_path)


@pytest.fixture(scope="session")
def valid_audit(bible, manuscript_path):
    from bookbible.manuscript import load_text

    return audit(bible, load_text(str(manuscript_path)))
