from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from telerag.ingestion.loader import DocumentLoader


class LoaderTests(unittest.TestCase):
    def test_supported_suffixes_include_html_and_markdown(self) -> None:
        self.assertIn(".html", DocumentLoader.SUPPORTED_SUFFIXES)
        self.assertIn(".htm", DocumentLoader.SUPPORTED_SUFFIXES)
        self.assertIn(".md", DocumentLoader.SUPPORTED_SUFFIXES)

    def test_html_loader_prefers_main_content(self) -> None:
        try:
            import bs4  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("beautifulsoup4 is not installed")

        loader = DocumentLoader()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            html_path = root / "page.html"
            html_path.write_text(
                """
                <html>
                  <body>
                    <nav>Menu</nav>
                    <main>
                      <h1>Qwen3 Guide</h1>
                      <p>Qwen3 is a language model family.</p>
                    </main>
                    <script>console.log("ignore me")</script>
                  </body>
                </html>
                """,
                encoding="utf-8",
            )

            documents = loader.load_path(html_path)

        self.assertEqual(len(documents), 1)
        self.assertIn("Qwen3 Guide", documents[0].text)
        self.assertIn("Qwen3 is a language model family.", documents[0].text)
        self.assertNotIn("Menu", documents[0].text)
        self.assertNotIn("ignore me", documents[0].text)

    def test_markdown_loader_keeps_headings_and_lists(self) -> None:
        try:
            import markdown_it  # noqa: F401
            import bs4  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("markdown/HTML parser deps are not installed")

        loader = DocumentLoader()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            md_path = root / "notes.md"
            md_path.write_text(
                """
                # Project Notes

                - First item
                - Second item

                ```python
                print("hello")
                ```
                """,
                encoding="utf-8",
            )

            documents = loader.load_path(md_path)

        self.assertEqual(len(documents), 1)
        self.assertIn("Project Notes", documents[0].text)
        self.assertIn("First item", documents[0].text)
        self.assertIn('print("hello")', documents[0].text)
