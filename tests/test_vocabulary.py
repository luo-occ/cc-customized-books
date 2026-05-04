import tempfile
import unittest
from pathlib import Path

from custom_epub.vocabulary import (
    find_glossary_matches,
    load_glossary_words,
    tokenize_english,
)


class VocabularyTests(unittest.TestCase):
    def test_load_glossary_words_ignores_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_text("tyranny\n\ncomrade\n", encoding="utf-8")

            self.assertEqual(load_glossary_words(path), {"tyranny", "comrade"})

    def test_find_glossary_matches_tokenizes_case_insensitively(self):
        words = {"tyranny", "comrade", "windmill"}
        text = "Comrade spoke against Tyranny near the WINDMILL."

        self.assertEqual(
            find_glossary_matches(text, words),
            ["comrade", "tyranny", "windmill"],
        )

    def test_tokenize_english_handles_apostrophes(self):
        self.assertEqual(
            tokenize_english("Animal's farm isn't quiet."),
            ["animal", "s", "farm", "isn", "t", "quiet"],
        )


if __name__ == "__main__":
    unittest.main()
