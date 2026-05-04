import unittest

from custom_epub.models import Pairing
from custom_epub.pairing import render_pairing_map, validate_pairings


class PairingTests(unittest.TestCase):
    def test_render_pairing_map_includes_rows_and_source_notes(self):
        rows = [
            Pairing(
                "Chapter One",
                "en/ch1.xhtml",
                "第一章",
                "zh/ch1.xhtml",
                "matched",
            )
        ]

        markdown = render_pairing_map(
            "Sample",
            rows,
            ["Chinese preface is visual-only."],
        )

        self.assertIn("# Sample Pairing Map", markdown)
        self.assertIn(
            "| Chapter One | `en/ch1.xhtml` | 第一章 | `zh/ch1.xhtml` | matched |",
            markdown,
        )
        self.assertIn("Chinese preface is visual-only.", markdown)

    def test_validate_pairings_rejects_missing_english_and_chinese_hrefs(self):
        rows = [
            Pairing(
                "Chapter One",
                "missing.xhtml",
                "第一章",
                "zh-missing.xhtml",
                "matched",
            )
        ]

        errors = validate_pairings(rows, {"en/ch1.xhtml"}, {"zh/ch1.xhtml"})

        self.assertEqual(
            errors,
            [
                "Chapter One references missing English href missing.xhtml",
                "Chapter One references missing Chinese href zh-missing.xhtml",
            ],
        )


if __name__ == "__main__":
    unittest.main()
