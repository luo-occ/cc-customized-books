from __future__ import annotations

import html
from importlib import resources

from .models import BookCompanion, CompanionChapter


def load_css() -> str:
    return resources.files("custom_epub.templates").joinpath("style.css").read_text(
        encoding="utf-8"
    )


def html_page(title: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{html.escape(title)}</title>
  <link href="style/main.css" rel="stylesheet" type="text/css"/>
</head>
<body>
{body}
</body>
</html>"""


def section_file_names(chapter_num: int) -> dict[str, str]:
    prefix = f"ch{chapter_num:02d}"
    return {
        "brief": f"{prefix}-brief.xhtml",
        "companion": f"{prefix}-companion.xhtml",
        "zh": f"{prefix}-zh.xhtml",
        "vocab": f"{prefix}-vocab.xhtml",
        "en": f"{prefix}-en.xhtml",
        "recap": f"{prefix}-recap.xhtml",
    }


def paragraphs(text: str) -> str:
    return "".join(
        f"<p>{html.escape(part.strip())}</p>"
        for part in text.split("\n\n")
        if part.strip()
    )


def _list_items(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def _teacher_section(title: str, content: str) -> str:
    if not content.strip():
        return ""
    return (
        f"<h2>{html.escape(title)}</h2>"
        f'<div class="teacher-section">{paragraphs(content)}</div>'
    )


def render_book_companion(title: str, companion: BookCompanion) -> str:
    teacher_mode = companion.teacher_mode
    teacher_blocks = ""
    if teacher_mode is not None:
        watch_block = ""
        if teacher_mode.what_to_watch:
            watch_block = (
                "<h2>What to watch / 阅读时要追踪什么</h2>"
                f"<ul>{_list_items(teacher_mode.what_to_watch)}</ul>"
            )
        question_block = ""
        if teacher_mode.questions_to_carry:
            question_block = (
                "<h2>Questions to carry / 带着走的问题</h2>"
                f"<ul>{_list_items(teacher_mode.questions_to_carry)}</ul>"
            )
        teacher_blocks = f"""
<h2>Central Thesis / 核心判断</h2>
<div class="teacher-section">
  <p>{html.escape(teacher_mode.central_thesis_zh)}</p>
  <p><strong>English:</strong> {html.escape(teacher_mode.central_thesis_en)}</p>
</div>
{_teacher_section("Why this book matters / 为什么值得读", teacher_mode.why_it_matters)}
{_teacher_section("Context frame / 阅读坐标", teacher_mode.context_frame)}
{_teacher_section("My take / 我的判断", teacher_mode.strong_interpretation)}
{_teacher_section("What this misses / 这一读法的盲点", teacher_mode.blind_spots)}
{watch_block}
{question_block}
"""
    return html_page(
        "Book Companion",
        f"""
<p class="eyebrow">Book Companion</p>
<h1>{html.escape(title)} / Book Companion</h1>
{paragraphs(companion.companion_zh)}
{teacher_blocks}
<h2>English Summary</h2>
<div class="english-summary"><p>{html.escape(companion.summary_en)}</p></div>
""",
    )


def render_chapter_pages(
    chapter_num: int,
    chinese_label: str,
    chapter: CompanionChapter,
    chinese_fragment: str,
    english_fragment: str,
) -> dict[str, str]:
    point_items = "".join(
        f"<li>{html.escape(point)}</li>" for point in chapter.listening_brief.points
    )
    vocab_sections = []
    for heading in [
        "Must know",
        "Useful / high-value",
        "Specialized or context-bound",
    ]:
        entries = "".join(
            f"<p>{html.escape(item)}</p>"
            for item in chapter.vocabulary.get(heading, [])
        )
        vocab_sections.append(f"<h2>{html.escape(heading)}</h2>{entries}")
    recap = chapter.recap
    lecture = chapter.mini_lecture
    lecture_block = ""
    if chapter.key_chapter and lecture is not None:
        question_block = ""
        if lecture.questions_to_carry:
            question_block = (
                "<h3>Questions to carry</h3>"
                f"<ul>{_list_items(lecture.questions_to_carry)}</ul>"
            )
        lecture_block = f"""
<h2>Mini Lecture / 深入讲解</h2>
<div class="teacher-section">
  <p><strong>Chapter thesis:</strong> {html.escape(lecture.chapter_thesis)}</p>
  <p><strong>Why it is pivotal:</strong> {html.escape(lecture.why_pivotal)}</p>
  <p><strong>Deeper interpretation:</strong> {html.escape(lecture.deeper_interpretation)}</p>
  <p><strong>Rival reading:</strong> {html.escape(lecture.rival_reading)}</p>
</div>
{question_block}
"""
    return {
        "brief": html_page(
            f"Chapter {chapter_num} Listening Brief",
            f"""
<p class="eyebrow">Chapter {chapter_num} Listening Brief</p>
<h1>Chapter {chapter_num} Listening Brief / {html.escape(chinese_label)} 听前提示</h1>
<div class="panel"><p><strong>Names:</strong> {html.escape(chapter.listening_brief.names)}</p><p>{html.escape(chapter.listening_brief.context)}</p></div>
<h2>What to listen for</h2>
<ul>{point_items}</ul>
""",
        ),
        "companion": html_page(
            f"Chapter {chapter_num} Companion Reference",
            f"""
<p class="eyebrow">Chapter {chapter_num} Companion Reference</p>
<h1>Chapter {chapter_num} Companion Reference / {html.escape(chinese_label)} 伴读参考</h1>
{paragraphs(chapter.companion.zh)}
<p class="priority">Reading priority: {html.escape(chapter.companion.priority)}</p>
{lecture_block}
<h2>English Summary</h2>
<div class="english-summary"><p>{html.escape(chapter.companion.en)}</p></div>
""",
        ),
        "zh": html_page(
            f"Chapter {chapter_num} Chinese",
            f"<h1>Chapter {chapter_num} Chinese / {html.escape(chinese_label)}</h1><div class=\"source-text\">{chinese_fragment}</div>",
        ),
        "vocab": html_page(
            f"Chapter {chapter_num} Vocabulary For Listening",
            f"<p class=\"eyebrow\">Chapter {chapter_num} Vocabulary For Listening</p><h1>Chapter {chapter_num} Vocabulary For Listening</h1>{''.join(vocab_sections)}",
        ),
        "en": html_page(
            f"Chapter {chapter_num} English",
            f"<h1>Chapter {chapter_num} English / {html.escape(chapter.english_label)}</h1><div class=\"source-text\">{english_fragment}</div>",
        ),
        "recap": html_page(
            f"Chapter {chapter_num} Recap",
            f"<p class=\"eyebrow\">Chapter {chapter_num} Recap</p><h1>Chapter {chapter_num} Recap</h1><div class=\"recap\"><p>{html.escape(recap.zh if recap else '')}</p><p><strong>English:</strong> {html.escape(recap.en if recap else '')}</p></div>",
        ),
    }
