from pathlib import Path
import unittest


class StaticAssetTests(unittest.TestCase):
    def _read_page(self, file_name: str) -> str:
        page_path = Path(__file__).resolve().parents[1] / "static" / file_name
        return page_path.read_text(encoding="utf-8")

    def test_app_page_uses_external_css_and_js(self):
        html = self._read_page("app.html")

        self.assertIn('href="/static/app.css"', html)
        self.assertIn('src="/static/app.js"', html)
        self.assertNotIn("<style>", html)
        self.assertNotIn("<script>", html)

    def test_form_page_uses_external_css_and_js(self):
        html = self._read_page("form.html")

        self.assertIn('href="/static/form.css"', html)
        self.assertIn('src="/static/form.js"', html)
        self.assertNotIn("<style>", html)
        self.assertNotIn("<script>", html)


if __name__ == "__main__":
    unittest.main()
