import unittest

from utils.language import find_non_us_english_spellings


class LanguageTests(unittest.TestCase):
    def test_finds_distinct_non_us_spellings(self):
        matches = find_non_us_english_spellings(
            "The organisation prioritises colour choices for the catalogue."
        )

        self.assertEqual(
            matches,
            ["organisation", "prioritises", "colour", "catalogue"],
        )

    def test_protects_official_names_and_avoids_us_false_positives(self):
        matches = find_non_us_english_spellings(
            "Colour Centre fulfills orders with a fulfilling support team.",
            ["Colour Centre"],
        )

        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
