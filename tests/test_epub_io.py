from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from custom_epub.epub_io import (
    clean_body_fragment,
    extract_cover_asset,
    extract_href_fragment,
    load_epub_structure,
    read_container_path,
)


CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


CONTENT_OPF = """<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Fixture Book</dc:title>
    <dc:language>en</dc:language>
    <meta name="cover" content="cover"/>
  </metadata>
  <manifest>
    <item id="ncx" href="Nav/toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="c1" href="Text/ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="Text/ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="cover" href="Images/cover.jpg" media-type="image/jpeg"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="cover"/>
    <itemref idref="c1"/>
    <itemref idref="c2"/>
  </spine>
</package>
"""


CONTENT_OPF_FRONTMATTER = """<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Fixture Book</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ncx" href="Nav/toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="title" href="Text/titlepage.xhtml" media-type="application/xhtml+xml"/>
    <item id="c1" href="Text/ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="front-cover" href="Images/front-cover.png" media-type="image/png"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="title"/>
    <itemref idref="c1"/>
  </spine>
</package>
"""


TOC_NCX = """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>Chapter One</text></navLabel>
      <content src="../Text/ch1.xhtml"/>
    </navPoint>
    <navPoint id="navPoint-2" playOrder="2">
      <navLabel><text>Chapter Two</text></navLabel>
      <content src="../Text/ch2.xhtml#start"/>
      <navPoint id="navPoint-2-1" playOrder="3">
        <navLabel><text>Chapter Two Note</text></navLabel>
        <content src="../Text/ch2.xhtml#note"/>
      </navPoint>
    </navPoint>
  </navMap>
</ncx>
"""


CHAPTER_ONE = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>Chapter One</h1>
    <p>First chapter.</p>
  </body>
</html>
"""


CHAPTER_TWO = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <section id="chapter-two">
      <div class="wrapper">
        <h1 id="start">Chapter Two</h1>
        <p id="note">Second chapter.</p>
      </div>
    </section>
    <div id="afterword">
      <p>Tail section.</p>
    </div>
  </body>
</html>
"""


TITLEPAGE = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <div class="cover">
      <img src="../Images/front-cover.png" alt="Cover"/>
    </div>
  </body>
</html>
"""


class EpubIoTests(unittest.TestCase):
    def _build_epub(
        self,
        root: Path,
        *,
        content_opf: str = CONTENT_OPF,
        extra_files: dict[str, str | bytes] | None = None,
    ) -> Path:
        epub_path = root / "fixture.epub"
        files: dict[str, str | bytes] = {
            "mimetype": "application/epub+zip",
            "META-INF/container.xml": CONTAINER_XML,
            "OPS/content.opf": content_opf,
            "OPS/Nav/toc.ncx": TOC_NCX,
            "OPS/Text/ch1.xhtml": CHAPTER_ONE,
            "OPS/Text/ch2.xhtml": CHAPTER_TWO,
            "OPS/Images/cover.jpg": b"jpeg-bytes",
        }
        if extra_files is not None:
            files.update(extra_files)
        with ZipFile(epub_path, "w", compression=ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(path, content)
        return epub_path

    def _build_frontmatter_cover_epub(self, root: Path) -> Path:
        return self._build_epub(
            root,
            content_opf=CONTENT_OPF_FRONTMATTER,
            extra_files={
                "OPS/Text/titlepage.xhtml": TITLEPAGE,
                "OPS/Images/front-cover.png": b"png-bytes",
            },
        )

    def test_read_container_path_finds_rootfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_epub(Path(tmp))

            with ZipFile(epub_path) as zf:
                self.assertEqual(read_container_path(zf), "OPS/content.opf")

    def test_load_epub_structure_reads_xhtml_spine_and_canonicalized_flattened_ncx(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_epub(Path(tmp))

            structure = load_epub_structure(epub_path)

            self.assertEqual(
                structure.spine,
                ["OPS/Text/ch1.xhtml", "OPS/Text/ch2.xhtml"],
            )
            self.assertEqual(
                [(entry.label, entry.href) for entry in structure.nav],
                [
                    ("Chapter One", "OPS/Text/ch1.xhtml"),
                    ("Chapter Two", "OPS/Text/ch2.xhtml"),
                    ("Chapter Two Note", "OPS/Text/ch2.xhtml"),
                ],
            )

    def test_clean_body_fragment_removes_scripts_and_unsafe_attrs_but_keeps_ids(self):
        raw = """
        <html>
          <body class="chapter-body" onload="evil()">
            <script>alert(1)</script>
            <style>body { color: red; }</style>
            <p id="frag" data-role="lead">
              Hello
              <a href="Text/ch1.xhtml#frag" title="jump" onclick="evil()">there</a>
              <img src="../Images/pic.jpg" alt="cover" onerror="boom()" />
            </p>
          </body>
        </html>
        """

        cleaned = clean_body_fragment(raw)

        self.assertNotIn("<script", cleaned)
        self.assertNotIn("<style", cleaned)
        self.assertNotIn("onload=", cleaned)
        self.assertNotIn("onclick=", cleaned)
        self.assertNotIn("onerror=", cleaned)
        self.assertNotIn("data-role=", cleaned)
        self.assertIn('id="frag"', cleaned)
        self.assertIn('href="Text/ch1.xhtml#frag"', cleaned)
        self.assertIn('src="../Images/pic.jpg"', cleaned)
        self.assertIn("Hello", cleaned)

    def test_extract_href_fragment_uses_nearest_body_child_and_following_siblings(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_epub(Path(tmp))

            fragment = extract_href_fragment(epub_path, "Text/ch2.xhtml#start")

            self.assertIn('id="chapter-two"', fragment)
            self.assertIn('id="start"', fragment)
            self.assertIn("Second chapter.", fragment)
            self.assertIn('id="afterword"', fragment)
            self.assertIn("Tail section.", fragment)

    def test_extract_href_fragment_raises_clear_error_when_fragment_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_epub(Path(tmp))

            with self.assertRaisesRegex(
                ValueError,
                "Fragment 'missing' not found in OPS/Text/ch2.xhtml",
            ):
                extract_href_fragment(epub_path, "Text/ch2.xhtml#missing")

    def test_extract_cover_asset_uses_explicit_metadata_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_epub(Path(tmp))

            cover = extract_cover_asset(epub_path)

            self.assertIsNotNone(cover)
            self.assertEqual(cover.href, "OPS/Images/cover.jpg")
            self.assertEqual(cover.media_type, "image/jpeg")
            self.assertEqual(cover.content, b"jpeg-bytes")

    def test_extract_cover_asset_falls_back_to_frontmatter_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = self._build_frontmatter_cover_epub(Path(tmp))

            cover = extract_cover_asset(epub_path)

            self.assertIsNotNone(cover)
            self.assertEqual(cover.href, "OPS/Images/front-cover.png")
            self.assertEqual(cover.media_type, "image/png")
            self.assertEqual(cover.content, b"png-bytes")


if __name__ == "__main__":
    unittest.main()
