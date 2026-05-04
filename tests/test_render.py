import unittest

from custom_epub.models import (
    BookCompanion,
    BookTeacherMode,
    ChapterCompanion,
    CompanionChapter,
    ListeningBrief,
    MiniLecture,
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

    def test_render_book_companion_omits_reference_section_from_listening_epub(self):
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
        self.assertIn("English Summary", rendered)
        self.assertNotIn("References For Visual Review", rendered)
        self.assertNotIn("Publisher page", rendered)
        self.assertNotIn("https://example.com/publisher", rendered)

    def test_render_book_companion_includes_teacher_mode_sections(self):
        companion = BookCompanion(
            companion_zh="基础导读",
            summary_en="English guide.",
            references=[],
            teacher_mode=BookTeacherMode(
                central_thesis_zh="真正的主题是语言与权力。",
                central_thesis_en="The real subject is language and power.",
                why_it_matters="它解释了理想如何被重新命名。",
                context_frame="放回革命政治史里理解。",
                strong_interpretation="最强的一点是模式而非影射。",
                blind_spots="它压缩了复杂社会差异。",
                what_to_watch=["注意口号变短。"],
                questions_to_carry=["谁在定义现实？"],
            ),
        )

        rendered = render_book_companion("Sample", companion)

        self.assertIn("Central Thesis / 核心判断", rendered)
        self.assertIn("真正的主题是语言与权力。", rendered)
        self.assertIn("The real subject is language and power.", rendered)
        self.assertIn("What this misses / 这一读法的盲点", rendered)
        self.assertIn("Questions to carry / 带着走的问题", rendered)
        self.assertNotIn("https://", rendered)

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

    def test_render_chapter_pages_includes_key_chapter_mini_lecture(self):
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
            key_chapter=True,
            mini_lecture=MiniLecture(
                chapter_thesis="这一章创建了政治语言。",
                why_pivotal="后面所有背叛都从这里分叉。",
                deeper_interpretation="它在讲革命如何先靠诗意成立。",
                rival_reading="也可读成神话式开端。",
                questions_to_carry=["诗意为什么会变成命令？"],
            ),
        )

        pages = render_chapter_pages(
            1,
            "第一章",
            chapter,
            "<p>中文正文</p>",
            "<p>English text.</p>",
        )

        self.assertIn("Mini Lecture / 深入讲解", pages["companion"])
        self.assertIn("这一章创建了政治语言。", pages["companion"])
        self.assertIn("诗意为什么会变成命令？", pages["companion"])


if __name__ == "__main__":
    unittest.main()
