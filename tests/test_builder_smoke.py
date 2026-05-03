import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from custom_epub.builder import build_project


def make_minimal_epub(path: Path, label: str, href: str, paragraph: str) -> None:
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
<manifest><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/><item id="ch1" href="{href}" media-type="application/xhtml+xml"/></manifest>
<spine toc="ncx"><itemref idref="ch1"/></spine></package>""",
        )
        zf.writestr(
            "OEBPS/toc.ncx",
            f"""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap><navPoint id="n1"><navLabel><text>{label}</text></navLabel><content src="{href}"/></navPoint></navMap></ncx>""",
        )
        zf.writestr(
            f"OEBPS/{href}",
            f"<html><body><h1>{label}</h1><p>{paragraph}</p></body></html>",
        )


class BuilderSmokeTests(unittest.TestCase):
    def test_build_project_creates_epub_and_pairing_map_without_listening_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            books = root / "books" / "Sample"
            project_dir = root / "book_projects" / "sample"
            books.mkdir(parents=True)
            project_dir.mkdir(parents=True)
            make_minimal_epub(
                books / "en.epub",
                "Chapter One",
                "Text/ch1.xhtml",
                "English text.",
            )
            make_minimal_epub(
                books / "zh.epub",
                "第一章",
                "Text/zh1.xhtml",
                "中文正文。",
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
                                "vocabulary": {
                                    "Must know": ["contrast, noun, 对比。"],
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

            result = build_project(project_dir, root)

            self.assertTrue(result.output_epub.exists())
            self.assertTrue(result.pairing_map.exists())
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
            self.assertNotIn("https://", xhtml)
            self.assertNotIn("References For Visual Review", xhtml)
            self.assertNotIn("Publisher page", xhtml)
            self.assertNotIn("English source text from", xhtml)
            self.assertNotIn("Chinese source text from", xhtml)
            pairing_map = result.pairing_map.read_text(encoding="utf-8")
            self.assertIn("# Sample Pairing Map", pairing_map)


if __name__ == "__main__":
    unittest.main()
