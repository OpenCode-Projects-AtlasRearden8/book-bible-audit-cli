"""Render the audit result as a Markdown report."""

from __future__ import annotations

from datetime import date

from .audit import AuditResult

SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


def render_report(
    result: AuditResult,
    manuscript_path: str,
    bible_path: str,
    repeat_threshold: int,
    llm_section: str = "",
) -> str:
    counts = result.counts_by_severity()
    characters = [e for e in result.entities if e["category"] == "character"]
    places = [e for e in result.entities if e["category"] == "place"]
    lines: list[str] = []
    add = lines.append

    add("# Manuscript Continuity Audit")
    add("")
    add(f"- Manuscript: `{manuscript_path}`")
    add(f"- Series bible: `{bible_path}`")
    add(f"- Generated: {date.today().isoformat()}")
    add(
        f"- Scope: {result.sentence_count} sentences, "
        f"{len(characters)} characters, {len(places)} places"
    )
    add("")
    add("## Summary")
    add("")
    add(
        f"- Findings: **{counts.get('high', 0)} high**, "
        f"{counts.get('medium', 0)} medium, {counts.get('info', 0)} info"
    )
    add(f"- Repeated phrases flagged (>= {repeat_threshold} occurrences): {len(result.repeats)}")
    add("")

    add("## Findings")
    add("")
    if not result.findings:
        add("None found.")
        add("")
    else:
        ordered = sorted(
            result.findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.kind, f.entity),
        )
        current_severity = None
        for finding in ordered:
            if finding.severity != current_severity:
                current_severity = finding.severity
                add(f"### {current_severity.title()}")
                add("")
            add(f"- **[{finding.kind}] {finding.entity}:** {finding.message}")
            if finding.detail:
                add(f"  > {finding.detail}")
        add("")

    add("## Character and place coverage")
    add("")
    if result.entities:
        add("| Entity | Category | Mentions | Bible eye color | Bible title | First seen | Died | Status |")
        add("|---|---|---:|---|---|---|---|---|")
        for entity in result.entities:
            add(
                f"| {entity['name']} | {entity['category']} | {entity['mentions']} | "
                f"{entity['eye_color'] or '-'} | {entity['title'] or '-'} | "
                f"{entity['first_seen'] or '-'} | {entity['died'] or '-'} | "
                f"{entity['status'] or '-'} |"
            )
    else:
        add("The bible has no entries.")
    add("")

    add("## Repeated phrases")
    add("")
    if result.repeats:
        add("| Phrase | Count |")
        add("|---|---:|")
        for repeat in result.repeats:
            add(f"| {repeat['phrase']} | {repeat['count']} |")
    else:
        add(f"None repeated {repeat_threshold} or more times.")
    add("")

    add("## Continuity notes from the bible")
    add("")
    if result.notes:
        for note in result.notes:
            add(f"- **{note['name']}** ({note['category']}): {note['notes']}")
    else:
        add("No notes in the bible.")
    add("")

    add("## Second opinion (LLM)")
    add("")
    add(llm_section.strip() if llm_section.strip() else "Skipped (run with `--llm` to enable).")
    add("")
    return "\n".join(lines) + "\n"
