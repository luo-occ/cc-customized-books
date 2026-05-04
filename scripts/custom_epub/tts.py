from __future__ import annotations

import re


RAW_URL_RE = re.compile(r"https?://[^\s<>()\[\]{}]+|www\.[^\s<>()\[\]{}]+")
TRAILING_URL_PUNCTUATION = ".,;:!?"


def find_raw_urls(text: str) -> list[str]:
    return [match.group(0).rstrip(TRAILING_URL_PUNCTUATION) for match in RAW_URL_RE.finditer(text)]


def validate_listener_text(section_name: str, text: str) -> list[str]:
    return [
        f"{section_name} contains raw listener-facing URL: {url}"
        for url in find_raw_urls(text)
    ]
