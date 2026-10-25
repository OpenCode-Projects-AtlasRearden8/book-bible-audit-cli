from __future__ import annotations

import pytest

from bookbible.audit import audit
from bookbible.bible import Bible, Entry, parse_bible
from bookbible.cli import main
from bookbible.report import render_report


def test_render_report_contains_all_sections(valid_audit, manuscript_path, sample_csv_bible_path):
    report = render_report(
        valid_audit,
        manuscript_path=str(manuscript_path),
        bible_path=str(sample_csv_bible_path),
        repeat_threshold=3,
    )
    for heading in (
        "# Manuscript Continuity Audit",
        "## Summary",
        "## Findings",
        "## Character and place coverage",
        "## Repeated phrases",
        "## Continuity notes from the bible",
        "## Second opinion (LLM)",
    ):
        assert heading in report
    assert "Lena" not in report
    assert "Elena Vance" in report


def test_render_report_empty_findings():
    bible = Bible(entries=[Entry(category="place", name="Oakbridge")])
    result = audit(bible, "Oakbridge sits on the river road.")
    report = render_report(
        result,
        manuscript_path="x.md",
        bible_path="b.csv",
        repeat_threshold=3,
        llm_section="Model says fine.",
    )
    assert "None found." in report
    assert "Model says fine." in report


def test_cli_writes_report(tmp_path, capsys, sample_csv_bible_path, manuscript_path):
    out = tmp_path / "report.md"
    code = main(
        [
            str(manuscript_path),
            "--bible",
            str(sample_csv_bible_path),
            "-o",
            str(out),
        ]
    )
    assert code == 0
    report = out.read_text(encoding="utf-8")
    assert "# Manuscript Continuity Audit" in report
    printed = capsys.readouterr().out
    assert "Wrote" in printed and "high" in printed


def test_cli_stdout_mode(capsys, sample_csv_bible_path, manuscript_path):
    code = main([str(manuscript_path), "--bible", str(sample_csv_bible_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert out.lstrip().startswith("# Manuscript Continuity Audit")


def test_cli_accepts_json_bible(tmp_path, sample_json_bible_path, manuscript_path):
    out = tmp_path / "report.md"
    assert main([str(manuscript_path), "--bible", str(sample_json_bible_path), "-o", str(out)]) == 0
    assert out.exists()


def test_cli_llm_failure_is_graceful(
    tmp_path, monkeypatch, sample_csv_bible_path, manuscript_path
):
    from bookbible import llm as llm_module

    def boom(*args, **kwargs):
        raise llm_module.LLMError("cannot reach http://localhost:11434/v1/chat/completions: refused")

    monkeypatch.setattr(llm_module, "review", boom)
    out = tmp_path / "report.md"
    code = main(
        [
            str(manuscript_path),
            "--bible",
            str(sample_csv_bible_path),
            "-o",
            str(out),
            "--llm",
        ]
    )
    assert code == 0
    assert "LLM second opinion skipped" in out.read_text(encoding="utf-8")


def test_cli_missing_manuscript_errors(sample_csv_bible_path):
    with pytest.raises(SystemExit) as exc:
        main(["no-such-file.md", "--bible", str(sample_csv_bible_path)])
    assert exc.value.code == 2


def test_cli_missing_bible_errors(manuscript_path):
    with pytest.raises(SystemExit) as exc:
        main([str(manuscript_path), "--bible", "no-such-bible.csv"])
    assert exc.value.code == 2


def test_cli_bad_bible_format_errors(sample_csv_bible_path, manuscript_path):
    with pytest.raises(SystemExit) as exc:
        main([str(manuscript_path), "--bible", str(sample_csv_bible_path) + ".txt"])
    assert exc.value.code == 2


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "bookbible" in capsys.readouterr().out


def test_parsed_sample_bible_is_loaded(sample_csv_bible_path):
    assert parse_bible(sample_csv_bible_path).entries
