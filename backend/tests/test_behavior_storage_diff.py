"""Tests for behavior/storage_diff.py — Storage Diff Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.severity import SeverityLevel
from app.behavior.storage_diff import compare_storage_snapshots


class TestStorageDiff:
    def test_auth_token_removed_triggers_high(self) -> None:
        base = [
            {
                "route": "/dashboard",
                "local_storage_keys": ["token", "theme"],
                "session_storage_keys": [],
                "cookie_names": [],
            }
        ]
        head = [
            {
                "route": "/dashboard",
                "local_storage_keys": ["theme"],
                "session_storage_keys": [],
                "cookie_names": [],
            }
        ]

        diffs = compare_storage_snapshots(base, head)
        token_diffs = [d for d in diffs if d.event_type == "LOCAL_STORAGE_KEY_REMOVED"]
        assert len(token_diffs) == 1
        assert token_diffs[0].severity == SeverityLevel.HIGH

    def test_theme_key_added_triggers_low(self) -> None:
        base = [
            {
                "route": "/",
                "local_storage_keys": [],
                "session_storage_keys": [],
                "cookie_names": [],
            }
        ]
        head = [
            {
                "route": "/",
                "local_storage_keys": ["theme"],
                "session_storage_keys": [],
                "cookie_names": [],
            }
        ]

        diffs = compare_storage_snapshots(base, head)
        added = [d for d in diffs if d.event_type == "LOCAL_STORAGE_KEY_ADDED"]
        assert len(added) == 1
        assert added[0].severity == SeverityLevel.LOW

    def test_cookie_removed_triggers_medium(self) -> None:
        base = [
            {
                "route": "/",
                "local_storage_keys": [],
                "session_storage_keys": [],
                "cookie_names": ["session_id"],
            }
        ]
        head = [
            {
                "route": "/",
                "local_storage_keys": [],
                "session_storage_keys": [],
                "cookie_names": [],
            }
        ]

        diffs = compare_storage_snapshots(base, head)
        removed_c = [d for d in diffs if d.event_type == "COOKIE_REMOVED"]
        assert len(removed_c) == 1
        assert removed_c[0].severity == SeverityLevel.MEDIUM
        assert removed_c[0].base_value["value"] == "[REDACTED]"
