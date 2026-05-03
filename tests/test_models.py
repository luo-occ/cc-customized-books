import json
import tempfile
import unittest
from pathlib import Path

from custom_epub.models import load_book_project, load_companion


class ModelLoadingTests(unittest.TestCase):
    def test_load_book_project_defaults_repo_root_from_project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved_root = root.resolve()
            project_dir = root / "book_projects" / "sample"
            project_dir.mkdir(parents=True)
            (project_dir / "project.json").write_text(
                json.dumps(
                    {
                        "slug": "sample",
                        "title": "Sample Book",
                        "author": "Author Name",
                        "sources": {
                            "english": "books/Sample/en.epub",
                        },
                        "output": {
                            "epub": "output/Sample/Sample.epub",
                            "pairing_map": "output/Sample/pairing-map.md",
                        },
                    }
                ),
                encoding="utf-8",
            )

            project = load_book_project(project_dir)

            self.assertEqual(project.repo_root, resolved_root)
            self.assertEqual(project.english_epub, resolved_root / "books/Sample/en.epub")
            self.assertEqual(project.output_epub, resolved_root / "output/Sample/Sample.epub")

    def test_load_book_project_resolves_paths_relative_to_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved_root = root.resolve()
            project_dir = root / "book_projects" / "sample"
            project_dir.mkdir(parents=True)
            (project_dir / "project.json").write_text(
                json.dumps(
                    {
                        "slug": "sample",
                        "title": "Sample Book",
                        "author": "Author Name",
                        "language": "en",
                        "description": "A sample bilingual project.",
                        "sources": {
                            "english": "books/Sample/en.epub",
                            "chinese": "books/Sample/zh.epub",
                        },
                        "output": {
                            "epub": "output/Sample/Sample.epub",
                            "pairing_map": "output/Sample/pairing-map.md",
                        },
                        "pairings": [
                            {
                                "english_label": "Chapter One",
                                "english_href": "Text/ch1.xhtml",
                                "chinese_label": "第一章",
                                "chinese_href": "Text/zh1.xhtml",
                                "status": "matched",
                            }
                        ],
                        "optional_sections": [
                            {
                                "title": "Optional Preface",
                                "source": "Chinese preface",
                                "href": "Text/preface.xhtml",
                                "action": "visual-only",
                                "language": "zh",
                                "intro": "Skip during first listening.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            project = load_book_project(project_dir, root)

            self.assertEqual(project.slug, "sample")
            self.assertEqual(project.title, "Sample Book")
            self.assertEqual(project.english_epub, resolved_root / "books/Sample/en.epub")
            self.assertEqual(project.chinese_epub, resolved_root / "books/Sample/zh.epub")
            self.assertEqual(project.output_epub, resolved_root / "output/Sample/Sample.epub")
            self.assertEqual(project.pairings[0].status, "matched")
            self.assertEqual(project.optional_sections[0].action, "visual-only")

    def test_load_companion_requires_book_and_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "中文导读",
                            "summary_en": "English guide",
                            "references": [{"label": "Publisher page"}],
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "listening_brief": {
                                    "names": "Old Major",
                                    "points": ["Listen for the speech."],
                                    "context": "Opening chapter.",
                                },
                                "companion": {
                                    "zh": "中文章节导读",
                                    "en": "English chapter summary.",
                                    "priority": "Read closely.",
                                },
                                "vocabulary": {
                                    "Must know": [
                                        "comrade, noun, 同志。A political address."
                                    ],
                                    "Useful / high-value": [],
                                    "Specialized or context-bound": [],
                                },
                                "recap": {
                                    "zh": "中文回顾",
                                    "en": "English recap.",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            companion = load_companion(project_dir)

            self.assertEqual(companion.book.companion_zh, "中文导读")
            self.assertEqual(companion.chapters[0].english_label, "Chapter One")
            self.assertEqual(
                companion.chapters[0].vocabulary["Must know"][0].split(",", 1)[0],
                "comrade",
            )

    def test_load_companion_rejects_non_list_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "中文导读",
                            "summary_en": "English guide",
                            "references": [],
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "listening_brief": {
                                    "names": "Old Major",
                                    "points": "Listen for the speech.",
                                    "context": "Opening chapter.",
                                },
                                "companion": {
                                    "zh": "中文章节导读",
                                    "en": "English chapter summary.",
                                },
                                "vocabulary": {
                                    "Must know": [],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                TypeError, "listening_brief.points must be a list"
            ):
                load_companion(project_dir)

    def test_load_companion_rejects_non_list_vocabulary_bucket(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "中文导读",
                            "summary_en": "English guide",
                            "references": [],
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "listening_brief": {
                                    "names": "Old Major",
                                    "points": ["Listen for the speech."],
                                    "context": "Opening chapter.",
                                },
                                "companion": {
                                    "zh": "中文章节导读",
                                    "en": "English chapter summary.",
                                },
                                "vocabulary": {
                                    "Must know": "comrade, noun, 同志。",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(TypeError, "vocabulary bucket 'Must know' must be a list"):
                load_companion(project_dir)


if __name__ == "__main__":
    unittest.main()
