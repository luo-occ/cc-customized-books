import unittest

from custom_epub.models import (
    BookCompanion,
    ChapterCompanion,
    CompanionChapter,
    ListeningBrief,
    Recap,
)
from custom_epub.render import (
    render_book_companion,
    render_chapter_pages,
    section_file_names,
)


class RenderTests(unittest.TestCase):
    def test_section_file_names_are_stable(self):
        names = section_file_names(1)

        self.assertEqual(names["brief"], "ch01-brief.xhtml")
        self.assertEqual(names["companion"], "ch01-companion.xhtml")
        self.assertEqual(names["zh"], "ch01-zh.xhtml")
        self.assertEqual(names["vocab"], "ch01-vocab.xhtml")
        self.assertEqual(names["en"], "ch01-en.xhtml")
        self.assertEqual(names["recap"], "ch01-recap.xhtml")

    def test_render_book_companion_uses_labels_not_raw_urls(self):
        companion = BookCompanion(
            companion_zh="中文导读",
            summary_en="English guide.",
            references=[
                {
                    "label": "Publisher page",
                    "url": "https://example.com/publisher",
                }
            ],
        )

        rendered = render_book_companion("Sample", companion)

        self.assertIn("Book Companion", rendered)
        self.assertIn("中文导读", rendered)
        self.assertIn("Publisher page", rendered)
        self.assertNotIn("https://example.com/publisher", rendered)

    def test_render_chapter_pages_has_expected_titles(self):
        chapter = CompanionChapter(
            english_label="Chapter One",
            listening_brief=ListeningBrief(
                names="Old Major",
                points=["Listen for slogans."],
                context="Opening.",
            ),
            companion=ChapterCompanion(
                zh="中文伴读",
                en="English summary.",
                priority="Read closely.",
            ),
            vocabulary={
                "Must know": ["comrade, noun, 同志。"],
                "Useful / high-value": [],
                "Specialized or context-bound": [],
            },
            recap=Recap(zh="中文回顾", en="English recap."),
        )

        pages = render_chapter_pages(
            1,
            "第一章",
            chapter,
            "<p>中文正文</p>",
            "<p>English text.</p>",
        )

        self.assertIn("Chapter 1 Listening Brief", pages["brief"])
        self.assertIn("Chapter 1 Companion Reference", pages["companion"])
        self.assertIn("Chapter 1 Chinese", pages["zh"])
        self.assertIn("Chapter 1 Vocabulary For Listening", pages["vocab"])
        self.assertIn("Chapter 1 English", pages["en"])
        self.assertIn("Chapter 1 Recap", pages["recap"])


if __name__ == "__main__":
    unittest.main()
