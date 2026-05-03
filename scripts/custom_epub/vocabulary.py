from __future__ import annotations

import re
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z]+")


def load_glossary_words(path: Path) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def tokenize_english(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def find_glossary_matches(text: str, glossary_words: set[str]) -> list[str]:
    tokens = set(tokenize_english(text))
    return sorted(tokens & {word.lower() for word in glossary_words})
