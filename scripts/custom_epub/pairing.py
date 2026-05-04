from __future__ import annotations

from .models import Pairing


def validate_pairings(
    pairings: list[Pairing],
    english_hrefs: set[str],
    chinese_hrefs: set[str],
) -> list[str]:
    errors: list[str] = []
    for row in pairings:
        if row.english_href not in english_hrefs:
            errors.append(
                f"{row.english_label} references missing English href {row.english_href}"
            )
        if row.chinese_href and row.chinese_href not in chinese_hrefs:
            errors.append(
                f"{row.english_label} references missing Chinese href {row.chinese_href}"
            )
    return errors


def render_pairing_map(
    title: str,
    rows: list[Pairing],
    source_notes: list[str],
) -> str:
    lines = [
        f"# {title} Pairing Map",
        "",
        "| English chapter | English source | Chinese chapter | Chinese source | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        chinese_label = row.chinese_label or ""
        chinese_href = f"`{row.chinese_href}`" if row.chinese_href else ""
        lines.append(
            f"| {row.english_label} | `{row.english_href}` | "
            f"{chinese_label} | {chinese_href} | {row.status} |"
        )

    if source_notes:
        lines.extend(["", "## Source inclusion notes", ""])
        lines.extend(f"- {note}" for note in source_notes)

    return "\n".join(lines) + "\n"
