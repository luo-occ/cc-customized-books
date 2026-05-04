import unittest

from custom_epub.tts import find_raw_urls, validate_listener_text


class TtsTests(unittest.TestCase):
    def test_find_raw_urls_detects_http_and_www(self):
        text = "Read https://example.com and www.example.org for more."

        self.assertEqual(
            find_raw_urls(text),
            ["https://example.com", "www.example.org"],
        )

    def test_validate_listener_text_reports_raw_urls(self):
        errors = validate_listener_text("Book Companion", "See https://example.com.")

        self.assertEqual(
            errors,
            ["Book Companion contains raw listener-facing URL: https://example.com"],
        )

    def test_validate_listener_text_allows_source_labels(self):
        self.assertEqual(
            validate_listener_text("Book Companion", "Source: publisher page."),
            [],
        )


if __name__ == "__main__":
    unittest.main()
