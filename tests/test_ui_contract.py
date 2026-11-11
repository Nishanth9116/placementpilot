"""Contract verification tests for PlacementPilot Frontend UI & Backend parity."""

import re
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent / "src" / "web" / "static"
HTML_PATH = WEB_DIR / "index.html"
JS_PATH = WEB_DIR / "js" / "app.js"
CSS_PATH = WEB_DIR / "css" / "style.css"


class TestUIContract:
    """Verifies that all views, buttons, forms, and onclick handlers are properly linked."""

    def test_static_files_exist(self):
        assert HTML_PATH.exists(), f"Missing index.html at {HTML_PATH}"
        assert JS_PATH.exists(), f"Missing app.js at {JS_PATH}"
        assert CSS_PATH.exists(), f"Missing style.css at {CSS_PATH}"

    def test_all_views_present_in_html(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        expected_views = [
            "view-dashboard",
            "view-applications",
            "view-companies",
            "view-calendar",
            "view-profile",
            "view-skillgap",
            "view-prep",
            "view-email",
        ]
        for v in expected_views:
            assert f'id="{v}"' in html, f"Missing view section: {v}"

    def test_all_modals_present_in_html(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        expected_modals = [
            "modal-apply",
            "modal-add-job",
            "modal-add-comp",
            "modal-schedule-round",
            "modal-record-outcome",
            "modal-view-rounds",
            "modal-job-analysis",
        ]
        for m in expected_modals:
            assert f'id="{m}"' in html, f"Missing modal dialog: {m}"

    def test_all_forms_present_in_html(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        expected_forms = [
            "student-profile-form",
            "mock-interview-form",
            "form-apply",
            "form-add-job",
            "form-add-comp",
            "form-schedule-round",
            "form-record-outcome",
        ]
        for f in expected_forms:
            assert f'id="{f}"' in html, f"Missing form: {f}"

    def test_onclick_handlers_defined_in_js(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        js = JS_PATH.read_text(encoding="utf-8")

        # Extract all onclick function calls: e.g. onclick="quickApply(1)" -> "quickApply"
        onclick_matches = re.findall(r'onclick=["\']([a-zA-Z0-9_]+)\(', html)
        unique_handlers = set(onclick_matches)

        for handler in unique_handlers:
            assert f"function {handler}" in js or f"{handler} = " in js or f"const {handler}" in js, (
                f"Handler '{handler}' invoked in HTML onclick but not defined in app.js"
            )

    def test_critical_button_ids_present(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        button_ids = [
            "btn-quick-apply",
            "btn-quick-add-job",
            "btn-add-skill",
            "btn-save-profile",
            "btn-run-skillgap",
            "btn-generate-email",
            "btn-copy-email",
        ]
        for b in button_ids:
            assert f'id="{b}"' in html, f"Missing button ID: {b}"

    def test_theme_css_custom_properties(self):
        css = CSS_PATH.read_text(encoding="utf-8")
        assert "--bg-base:" in css
        assert "--accent-blue:" in css
        assert "--border-subtle:" in css
        assert "dialog.custom-modal" in css

