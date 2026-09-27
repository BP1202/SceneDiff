"""Tests for the Diff Parser Engine (services/diff_parser.py)."""

import pytest

from app.services.diff_parser import Language, parse_diff

_PYTHON_DIFF = """\
diff --git a/app/handler.py b/app/handler.py
--- a/app/handler.py
+++ b/app/handler.py
@@ -1,7 +1,9 @@
 import os

-def handle_request(req):
+def handle_request(req, timeout=30):
     x = 1
-    return x
+    # New implementation
+    return x + timeout
"""

_TS_DIFF = """\
diff --git a/src/api.ts b/src/api.ts
--- a/src/api.ts
+++ b/src/api.ts
@@ -1,5 +1,7 @@
 import { Response } from 'express';

-function fetchData(url: string): Promise<Response> {
+async function fetchData(url: string, opts?: object): Promise<Response> {
     return fetch(url);
+
 }
"""

_JS_DIFF = """\
diff --git a/src/utils.js b/src/utils.js
--- a/src/utils.js
+++ b/src/utils.js
@@ -1,4 +1,6 @@
-function formatDate(d) {
+function formatDate(d, locale) {
     return d.toISOString();
 }
+
+function newHelper() { return 42; }
"""

_MULTI_FILE_DIFF = _PYTHON_DIFF + "\n" + _TS_DIFF

_EMPTY_DIFF = ""

_NEW_FILE_DIFF = """\
diff --git a/app/new_module.py b/app/new_module.py
--- /dev/null
+++ b/app/new_module.py
@@ -0,0 +1,4 @@
+def new_function():
+    return True
"""


class TestParseDiff:
    """Tests for parse_diff top-level function."""

    def test_empty_diff_returns_empty_list(self) -> None:
        assert parse_diff(_EMPTY_DIFF) == []

    def test_python_diff_returns_one_entry(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        assert len(results) == 1

    def test_python_language_detected(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        assert results[0].language == Language.PYTHON

    def test_python_file_path_extracted(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        assert results[0].file_path == "app/handler.py"

    def test_python_modified_function_detected(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        assert "handle_request" in results[0].modified_functions

    def test_typescript_language_detected(self) -> None:
        results = parse_diff(_TS_DIFF)
        assert results[0].language == Language.TYPESCRIPT

    def test_typescript_file_path_extracted(self) -> None:
        results = parse_diff(_TS_DIFF)
        assert results[0].file_path == "src/api.ts"

    def test_javascript_added_function_detected(self) -> None:
        results = parse_diff(_JS_DIFF)
        assert "newHelper" in results[0].added_functions

    def test_multi_file_diff_returns_multiple_entries(self) -> None:
        results = parse_diff(_MULTI_FILE_DIFF)
        assert len(results) == 2

    def test_new_file_from_dev_null(self) -> None:
        results = parse_diff(_NEW_FILE_DIFF)
        assert len(results) == 1
        assert results[0].file_path == "app/new_module.py"
        assert "new_function" in results[0].added_functions

    def test_line_numbers_present_for_changed_file(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        assert len(results[0].line_numbers) > 0

    def test_hunks_present(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        assert len(results[0].hunks) == 1

    def test_hunk_added_lines_not_empty(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        hunk = results[0].hunks[0]
        assert len(hunk.added_lines) > 0

    def test_hunk_removed_lines_not_empty(self) -> None:
        results = parse_diff(_PYTHON_DIFF)
        hunk = results[0].hunks[0]
        assert len(hunk.removed_lines) > 0

    def test_unknown_extension_returns_unknown_language(self) -> None:
        diff = """\
diff --git a/config.yaml b/config.yaml
--- a/config.yaml
+++ b/config.yaml
@@ -1,2 +1,2 @@
-version: 1
+version: 2
"""
        results = parse_diff(diff)
        assert results[0].language == Language.UNKNOWN

    def test_parsed_diff_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        results = parse_diff(_PYTHON_DIFF)
        with pytest.raises(FrozenInstanceError):
            results[0].file_path = "other.py"  # type: ignore[misc]
