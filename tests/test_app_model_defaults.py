from pathlib import Path
import unittest


class FaqAppModelDefaultsTests(unittest.TestCase):
    def test_app_displays_shared_model_defaults(self):
        source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("DEFAULT_MODELS", source)
        self.assertIn('DEFAULT_MODELS["OpenAI"]', source)


if __name__ == "__main__":
    unittest.main()
