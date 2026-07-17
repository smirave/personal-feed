import unittest
from pathlib import Path

from app.services.prompt_manager import PromptManager


class PromptManagerTests(unittest.TestCase):
    def test_list_prompts_discovers_markdown_files(self):
        manager = PromptManager(base_dir=Path(__file__).resolve().parents[1])

        prompts = manager.list_prompts()

        self.assertGreaterEqual(len(prompts), 3)
        self.assertIn("cybersecurity.md", {prompt["file"] for prompt in prompts})
        self.assertTrue(any(prompt["name"] for prompt in prompts))

    def test_load_prompt_returns_content(self):
        manager = PromptManager(base_dir=Path(__file__).resolve().parents[1])

        content = manager.load_prompt("cybersecurity.md")

        self.assertIn("Title:", content)
        self.assertIn("cybersecurity", content.lower())


if __name__ == "__main__":
    unittest.main()
