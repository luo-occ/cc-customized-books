import json
import tempfile
import unittest
from pathlib import Path
from typing import Optional, Tuple
from zipfile import ZipFile

from custom_epub.builder import build_project


def make_minimal_epub(
    path: Path,
    label: str,
    href: str,
    paragraph: str,
    *,
    cover_href: Optional[str] = None,
    cover_media_type: Optional[str] = None,
    cover_content: Optional[bytes] = None,
    metadata_cover_id: str = "cover",
    body_html: Optional[str] = None,
    extra_files: Optional[list[tuple[str, bytes]]] = None,
) -> None:
    manifest_items = [
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        f'<item id="ch1" href="{href}" media-type="application/xhtml+xml"/>',
    ]
    metadata = ""
    if cover_href is not None:
        if cover_media_type is None or cover_content is None:
            raise ValueError("Cover media type and content are required with cover_href")
        manifest_items.append(
            f'<item id="{metadata_cover_id}" href="{cover_href}" media-type="{cover_media_type}"/>'
        )
        metadata = f'<metadata><meta name="cover" content="{metadata_cover_id}"/></metadata>'

    with ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
{metadata}<manifest>{''.join(manifest_items)}</manifest>
<spine toc="ncx"><itemref idref="ch1"/></spine></package>""",
        )
        zf.writestr(
            "OEBPS/toc.ncx",
            f"""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap><navPoint id="n1"><navLabel><text>{label}</text></navLabel><content src="{href}"/></navPoint></navMap></ncx>""",
        )
        zf.writestr(
            f"OEBPS/{href}",
            body_html or f"<html><body><h1>{label}</h1><p>{paragraph}</p></body></html>",
        )
        if cover_href is not None and cover_content is not None:
            zf.writestr(f"OEBPS/{cover_href}", cover_content)
        for extra_path, extra_content in extra_files or []:
            zf.writestr(extra_path, extra_content)


class BuilderSmokeTests(unittest.TestCase):
    def _write_project_fixture(
        self,
        root: Path,
        *,
        english_cover: Optional[Tuple[str, str, bytes]] = None,
        chinese_cover: Optional[Tuple[str, str, bytes]] = None,
    ) -> Path:
        books = root / "books" / "Sample"
        project_dir = root / "book_projects" / "sample"
        books.mkdir(parents=True)
        project_dir.mkdir(parents=True)
        english_kwargs = {}
        chinese_kwargs = {}
        if english_cover is not None:
            english_kwargs = {
                "cover_href": english_cover[0],
                "cover_media_type": english_cover[1],
                "cover_content": english_cover[2],
            }
        if chinese_cover is not None:
            chinese_kwargs = {
                "cover_href": chinese_cover[0],
                "cover_media_type": chinese_cover[1],
                "cover_content": chinese_cover[2],
            }
        make_minimal_epub(
            books / "en.epub",
            "Chapter One",
            "Text/ch1.xhtml",
            "English text.",
            **english_kwargs,
        )
        make_minimal_epub(
            books / "zh.epub",
            "第一章",
            "Text/zh1.xhtml",
            "动物们一齐向前冲去，谁也不再等待命令，他们知道这一刻已经不能回头。",
            **chinese_kwargs,
        )
        (project_dir / "project.json").write_text(
            json.dumps(
                {
                    "slug": "sample",
                    "title": "Sample",
                    "author": "Author",
                    "language": "en",
                    "description": "Sample build.",
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
                            "english_href": "OEBPS/Text/ch1.xhtml",
                            "chinese_label": "第一章",
                            "chinese_href": "OEBPS/Text/zh1.xhtml",
                            "status": "matched",
                        }
                    ],
                    "optional_sections": [],
                }
            ),
            encoding="utf-8",
        )
        (project_dir / "companion.json").write_text(
            json.dumps(
                {
                    "book": {
                        "companion_zh": "中文导读",
                        "summary_en": "English summary.",
                        "references": [{"label": "Publisher page"}],
                        "teacher_mode": {
                            "central_thesis": {
                                "zh": "这本书考察语言和权力。",
                                "en": "This book studies language and power.",
                            },
                            "why_it_matters": "它解释理想如何被权力接管。",
                            "context_frame": "放回革命政治史里理解。",
                            "strong_interpretation": "它最强的是模式，不是单纯影射。",
                            "blind_spots": "它压缩了复杂社会层次。",
                            "what_to_watch": ["注意谁在解释现实。"],
                            "questions_to_carry": ["谁在定义现实？"],
                        },
                    },
                    "chapters": [
                        {
                            "english_label": "Chapter One",
                            "key_chapter": True,
                            "listening_brief": {
                                "names": "Name",
                                "points": ["Listen for contrast."],
                                "context": "Context.",
                            },
                            "companion": {
                                "zh": "中文伴读",
                                "en": "English companion.",
                                "priority": "Read closely.",
                            },
                            "vocabulary": {
                                "Must know": ["contrast, noun, 对比。"],
                                "Useful / high-value": [],
                                "Specialized or context-bound": [],
                            },
                            "mini_lecture": {
                                "chapter_thesis": "这一章建立政治词汇。",
                                "why_pivotal": "后面的背叛都从这里开始。",
                                "deeper_interpretation": "革命先靠语言成立。",
                                "rival_reading": "也可以读成神话化开端。",
                                "questions_to_carry": ["诗意为什么会变成命令？"],
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
        return project_dir

    def test_build_project_creates_epub_and_pairing_map_without_listening_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = self._write_project_fixture(root)

            result = build_project(project_dir, root)

            self.assertTrue(result.output_epub.exists())
            self.assertTrue(result.pairing_map.exists())
            self.assertEqual(
                result.warnings,
                ["No extractable cover found in English or Chinese source EPUBs."],
            )
            with ZipFile(result.output_epub) as zf:
                names = zf.namelist()
                self.assertIn("EPUB/book-companion.xhtml", names)
                self.assertIn("EPUB/ch01-brief.xhtml", names)
                self.assertIn("EPUB/ch01-vocab.xhtml", names)
                xhtml = "\n".join(
                    zf.read(name).decode("utf-8")
                    for name in names
                    if name.endswith(".xhtml")
                )
            self.assertIn("Chapter 1 Listening Brief", xhtml)
            self.assertIn("Chapter 1 Companion Reference", xhtml)
            self.assertIn("Central Thesis / 核心判断", xhtml)
            self.assertIn("Questions to carry / 带着走的问题", xhtml)
            self.assertIn("Mini Lecture / 深入讲解", xhtml)
            self.assertIn("谁在定义现实？", xhtml)
            self.assertIn("诗意为什么会变成命令？", xhtml)
            self.assertNotIn("https://", xhtml)
            self.assertNotIn("References For Visual Review", xhtml)
            self.assertNotIn("Publisher page", xhtml)
            self.assertNotIn("English source text from", xhtml)
            self.assertNotIn("Chinese source text from", xhtml)
            pairing_map = result.pairing_map.read_text(encoding="utf-8")
            self.assertIn("# Sample Pairing Map", pairing_map)

    def test_build_project_inherits_english_cover_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            english_cover = ("Images/en-cover.jpg", "image/jpeg", b"english-cover-bytes")
            chinese_cover = ("Images/zh-cover.png", "image/png", b"chinese-cover-bytes")
            project_dir = self._write_project_fixture(
                root,
                english_cover=english_cover,
                chinese_cover=chinese_cover,
            )

            result = build_project(project_dir, root)

            self.assertEqual(result.warnings, [])
            with ZipFile(result.output_epub) as zf:
                names = zf.namelist()
                self.assertIn("EPUB/Images/en-cover.jpg", names)
                self.assertEqual(
                    zf.read("EPUB/Images/en-cover.jpg"), b"english-cover-bytes"
                )
                self.assertNotIn("EPUB/Images/zh-cover.png", names)
                content_opf = zf.read("EPUB/content.opf").decode("utf-8")
            self.assertIn('name="cover"', content_opf)

    def test_build_project_falls_back_to_chinese_cover_when_english_has_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chinese_cover = ("Images/zh-cover.png", "image/png", b"chinese-cover-bytes")
            project_dir = self._write_project_fixture(
                root,
                chinese_cover=chinese_cover,
            )

            result = build_project(project_dir, root)

            self.assertEqual(result.warnings, [])
            with ZipFile(result.output_epub) as zf:
                names = zf.namelist()
                self.assertIn("EPUB/Images/zh-cover.png", names)
                self.assertEqual(
                    zf.read("EPUB/Images/zh-cover.png"), b"chinese-cover-bytes"
                )
                content_opf = zf.read("EPUB/content.opf").decode("utf-8")
            self.assertIn('name="cover"', content_opf)

    def test_build_project_embeds_assets_for_image_only_chinese_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            books = root / "books" / "Sample"
            project_dir = self._write_project_fixture(root)
            (project_dir / "companion.json").write_text(
                json.dumps(
                    {
                        "book": {
                            "companion_zh": "中文导读",
                            "summary_en": "English summary.",
                            "references": [{"label": "Publisher page"}],
                            "teacher_mode": {
                                "central_thesis": {
                                    "zh": "这本书考察语言和权力。",
                                    "en": "This book studies language and power.",
                                },
                                "why_it_matters": "它解释理想如何被权力接管。",
                                "context_frame": "放回革命政治史里理解。",
                                "strong_interpretation": "它最强的是模式，不是单纯影射。",
                                "blind_spots": "它压缩了复杂社会层次。",
                                "what_to_watch": ["注意谁在解释现实。"],
                                "questions_to_carry": ["谁在定义现实？"],
                            },
                        },
                        "chapters": [
                            {
                                "english_label": "Chapter One",
                                "listening_brief": {
                                    "names": "Name",
                                    "points": ["Listen for contrast."],
                                    "context": "Context.",
                                },
                                "companion": {
                                    "zh": "中文伴读",
                                    "en": "English companion.",
                                    "priority": "Read closely.",
                                },
                                "chinese_text": {
                                    "mode": "generated_translation",
                                    "content": "这是代理生成的中文译文。\n\n它应该出现在中文章节正文里。",
                                    "reason": "image_only_source",
                                },
                                "vocabulary": {
                                    "Must know": ["contrast, noun, 对比。"],
                                    "Useful / high-value": [],
                                    "Specialized or context-bound": [],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            make_minimal_epub(
                books / "zh.epub",
                "第一章",
                "Text/zh1.xhtml",
                "unused",
                body_html=(
                    '<html><body><p class="center">'
                    '<img alt="" src="../Images/zh-page.png"/>'
                    "</p></body></html>"
                ),
                extra_files=[("OEBPS/Images/zh-page.png", b"fake-image-bytes")],
            )

            result = build_project(project_dir, root)

            self.assertNotIn("Chinese chapter '第一章' is image-only", result.warnings)
            with ZipFile(result.output_epub) as zf:
                names = zf.namelist()
                self.assertNotIn("EPUB/assets/ch01-zh-01.png", names)
                zh_page = zf.read("EPUB/ch01-zh.xhtml").decode("utf-8")
            self.assertIn("这是代理生成的中文译文。", zh_page)
            self.assertIn("它应该出现在中文章节正文里。", zh_page)
            self.assertNotIn("<img", zh_page)


if __name__ == "__main__":
    unittest.main()
