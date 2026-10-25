"""Optional LLM second opinion via any OpenAI-compatible chat endpoint.

Default target is a local, keyless Ollama server (http://localhost:11434/v1).
An API key is never required; if one is set (flag or BOOKBIBLE_API_KEY env var)
it is only sent as a Bearer header and never written to files or logs.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3"
DEFAULT_TIMEOUT = 120.0
MAX_EXCERPT_CHARS = 6000

SYSTEM_PROMPT = (
    "You are a careful continuity editor. You are given a series bible summary "
    "and the beginning of a manuscript. List any continuity problems you notice "
    "(eye colors, titles, dates or days, characters who should be dead, repeated "
    "phrasing, place names). Be concrete and quote the text. If you find nothing, "
    "say so plainly."
)


class LLMError(RuntimeError):
    pass


def build_payload(bible, result, text: str, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    bible_lines = []
    for entry in bible.entries:
        parts = [f"{entry.category} {entry.name}"]
        if entry.aliases:
            parts.append(f"(aka {', '.join(entry.aliases)})")
        if entry.eye_color:
            parts.append(f"eyes={entry.eye_color}")
        if entry.title:
            parts.append(f"title={entry.title}")
        if entry.first_seen:
            parts.append(f"first seen {entry.first_seen}")
        if entry.died:
            parts.append(f"died {entry.died}")
        bible_lines.append("; ".join(parts))

    finding_lines = [f"- [{f.severity}] {f.kind}: {f.message}" for f in result.findings]
    excerpt = text[:max_chars]
    return "\n".join(
        [
            "SERIES BIBLE:",
            *(bible_lines or ["(no entries)"]),
            "",
            "AUDIT FINDINGS SO FAR:",
            *(finding_lines or ["(none)"]),
            "",
            "MANUSCRIPT EXCERPT:",
            excerpt,
        ]
    )


def _post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def review(
    payload: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    message = {"role": "user", "content": payload}
    body = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, message],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        raw = _post(url, body, headers, timeout)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read(300).decode("utf-8", "replace").strip()
        except Exception:
            detail = ""
        suffix = f": {detail}" if detail else ""
        raise LLMError(f"endpoint returned HTTP {exc.code}{suffix}") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise LLMError(f"cannot reach {url}: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"unexpected response from {url}") from exc
    if not content or not content.strip():
        raise LLMError(f"empty response from {url}")
    return content.strip()


def resolve_api_key(cli_value: str | None) -> str | None:
    return cli_value or os.environ.get("BOOKBIBLE_API_KEY") or None
