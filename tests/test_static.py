"""Static-asset checks: CS-B10 (client side), CS-B12, CS-B14, plus serving of the page."""

import re
import unittest
from pathlib import Path

try:
    from helpers import ServerCase
except ImportError:
    from tests.helpers import ServerCase

STATIC = Path(__file__).resolve().parent.parent / "case_study_builder" / "static"


def read(name):
    return (STATIC / name).read_text(encoding="utf-8")


class StaticAssets(unittest.TestCase):
    def test_b12_no_external_urls(self):
        for name in ("index.html", "app.css", "app.js"):
            text = read(name)
            self.assertIsNone(re.search(r"https?://", text), name)
            self.assertIsNone(re.search(r"""(?:src|href)\s*=\s*["']//""", text), name)
            self.assertNotIn("@import", text, name)
            self.assertNotIn("@font-face", text, name)

    def test_csp_compatible_html(self):
        html = read("index.html")
        self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)")
        self.assertNotRegex(html, r"\sstyle\s*=")
        self.assertNotRegex(html, r"\son[a-z]+\s*=")
        self.assertNotIn("<style", html)

    def test_b10_client_never_injects_html(self):
        js = read("app.js")
        for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
            self.assertNotIn(banned, js)
        self.assertNotRegex(js, r"\.style\.cssText|setAttribute\(\s*['\"]style")

    def test_b14_labels_and_controls_present(self):
        html, js = read("index.html"), read("app.js")
        for needle in ('for="title"', "Case study title", 'id="add-section"', "Add section", 'id="save"',
                       ">Save<", 'id="project-list"', 'id="new-project"', 'id="preview"',
                       'role="status"', 'aria-live="polite"', 'role="alert"', 'aria-label="Case studies"',
                       'aria-label="Case study editor"', 'aria-label="Reading preview"', 'id="reload"'):
            self.assertIn(needle, html)
        for needle in ("Move section", "Delete section", '" up"', '" down"', '" heading"', '" body"',
                       'e.key === "s"', "ArrowUp", "ArrowDown", "altKey", "ctrlKey", "metaKey", "beforeunload", "textContent"):
            self.assertIn(needle, js)

    def test_focus_and_responsive_rules_present(self):
        css = read("app.css")
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("@media", css)


class ServedPage(ServerCase):
    def test_index_and_assets_served_with_types(self):
        status, resp, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        self.assertIn(b"Case study title", body)
        status, resp, _ = self.request("GET", "/static/app.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", resp.getheader("Content-Type"))
        status, resp, _ = self.request("GET", "/static/app.css")
        self.assertEqual(status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/css"))
        self.assertIn("script-src 'self'", resp.getheader("Content-Security-Policy"))


if __name__ == "__main__":
    unittest.main()
