import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from custom_epub.epub_io import (
    clean_body_fragment,
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


class EpubIoTests(unittest.TestCase):
    def _build_epub(self, root: Path) -> Path:
        epub_path = root / "fixture.epub"
        with ZipFile(epub_path, "w", compression=ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", CONTAINER_XML)
            zf.writestr("OPS/content.opf", CONTENT_OPF)
            zf.writestr("OPS/Nav/toc.ncx", TOC_NCX)
            zf.writestr("OPS/Text/ch1.xhtml", CHAPTER_ONE)
            zf.writestr("OPS/Text/ch2.xhtml", CHAPTER_TWO)
            zf.writestr("OPS/Images/cover.jpg", b"jpeg-bytes")
        return epub_path

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


if __name__ == "__main__":
    unittest.main()
