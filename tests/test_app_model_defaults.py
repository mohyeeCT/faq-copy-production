from pathlib import Path
import unittest


class FaqAppModelDefaultsTests(unittest.TestCase):
    def test_app_displays_shared_model_defaults(self):
        source = Path("app.py").read_text(encoding="utf-8")

        self.assertIn("DEFAULT_MODELS", source)
        self.assertIn('DEFAULT_MODELS["Claude"]', source)
        self.assertIn('DEFAULT_MODELS["OpenAI"]', source)
        self.assertIn("claude-sonnet-5", source)
        self.assertIn("claude-sonnet-4-6", source)
        self.assertIn("claude-haiku-4-5-20251001", source)
        self.assertIn("gpt-5.5", source)
        self.assertIn("gpt-5.4", source)
        self.assertIn("gemini-3.5-flash", source)
        self.assertNotIn("Mistral", source)
        self.assertNotIn("Groq", source)
        self.assertNotIn("gemini-2.0-flash", source)
        self.assertNotIn("gpt-4o", source)
        self.assertNotIn("gpt-5.4-mini", source)
        self.assertNotIn("gpt-5.4-nano", source)


if __name__ == "__main__":
    unittest.main()
