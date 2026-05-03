#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from custom_epub.builder import build_project


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a customized bilingual study EPUB."
    )
    parser.add_argument(
        "project_dir",
        type=Path,
        help="Path to a book project directory containing project.json and companion.json",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root used to resolve relative paths",
    )
    args = parser.parse_args()

    result = build_project(args.project_dir, args.repo_root)
    print(f"EPUB: {result.output_epub}")
    print(f"Pairing map: {result.pairing_map}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
