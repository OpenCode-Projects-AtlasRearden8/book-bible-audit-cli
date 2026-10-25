from __future__ import annotations

import json
from urllib.error import HTTPError, URLError

import pytest

from bookbible import llm
from bookbible.bible import parse_bible
from bookbible.manuscript import load_text
from bookbible.llm import LLMError, build_payload, resolve_api_key, review


class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def completion(content: str = "Looks consistent overall.") -> bytes:
    body = {"choices": [{"message": {"role": "assistant", "content": content}}]}
    return json.dumps(body).encode("utf-8")


def test_review_returns_content(monkeypatch):
    captured = {}

    def fake_post(url, body, headers, timeout):
        captured["url"] = url
        captured["body"] = json.loads(body.decode("utf-8"))
        return completion("No continuity issues found.")

    monkeypatch.setattr(llm, "_post", fake_post)
    out = review("hello", api_key="secret-key")
    assert out == "No continuity issues found."
    assert captured["url"].endswith("/chat/completions")
    assert captured["body"]["messages"][0]["role"] == "system"
    assert captured["body"]["model"] == llm.DEFAULT_MODEL
    assert not captured["body"].get("api_key")


def test_review_sends_bearer_header(monkeypatch):
    seen = {}

    def fake_post(url, body, headers, timeout):
        seen.update(headers)
        return completion()

    monkeypatch.setattr(llm, "_post", fake_post)
    review("payload", api_key="abc")
    assert seen["Authorization"] == "Bearer abc"


def test_review_connection_error(monkeypatch):
    def fake_post(url, body, headers, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr(llm, "_post", fake_post)
    with pytest.raises(LLMError, match="cannot reach"):
        review("payload")


def test_review_http_error(monkeypatch):
    def fake_post(url, body, headers, timeout):
        raise HTTPError(url, 500, "boom", None, None)

    monkeypatch.setattr(llm, "_post", fake_post)
    with pytest.raises(LLMError, match="HTTP 500"):
        review("payload")


def test_review_unexpected_shape(monkeypatch):
    monkeypatch.setattr(llm, "_post", lambda *a, **k: b'{"nope": true}')
    with pytest.raises(LLMError, match="unexpected response"):
        review("payload")


def test_review_empty_content(monkeypatch):
    monkeypatch.setattr(llm, "_post", lambda *a, **k: completion("   "))
    with pytest.raises(LLMError, match="empty response"):
        review("payload")


def test_resolve_api_key_prefers_cli(monkeypatch):
    monkeypatch.setenv("BOOKBIBLE_API_KEY", "env-key")
    assert resolve_api_key("cli-key") == "cli-key"
    assert resolve_api_key(None) == "env-key"
    monkeypatch.delenv("BOOKBIBLE_API_KEY")
    assert resolve_api_key(None) is None


def test_build_payload_contains_bible_and_findings(bible, manuscript_path, valid_audit):
    text = load_text(str(manuscript_path))
    payload = build_payload(bible, valid_audit, text, max_chars=200)
    assert "Elena Vance" in payload
    assert "eye-color" in payload or "timeline" in payload


def test_parse_json_bible_module(sample_json_bible_path):
    bible = parse_bible(sample_json_bible_path)
    payload = build_payload(bible, type("R", (), {"findings": []})(), "text")
    assert "Marta Halloran" in payload
