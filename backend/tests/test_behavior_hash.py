"""Tests for the Behavior Hash Engine (services/behavior_hash.py)."""

from app.services.behavior_hash import generate_behavior_hash, hash_metadata


class TestGenerateBehaviorHash:
    """Unit tests for generate_behavior_hash."""

    def test_returns_64_char_hex_string(self) -> None:
        h = generate_behavior_hash("src/app.py", "my_func", "- x = 1\n+ x = 2")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_inputs_produce_same_hash(self) -> None:
        h1 = generate_behavior_hash("src/app.py", "my_func", "- x = 1\n+ x = 2")
        h2 = generate_behavior_hash("src/app.py", "my_func", "- x = 1\n+ x = 2")
        assert h1 == h2

    def test_whitespace_differences_produce_same_hash(self) -> None:
        h1 = generate_behavior_hash("src/app.py", "fn", "x = 1")
        h2 = generate_behavior_hash("src/app.py", "fn", "x  =  1")
        assert h1 == h2

    def test_comment_lines_ignored(self) -> None:
        h1 = generate_behavior_hash("src/app.py", "fn", "x = 1")
        h2 = generate_behavior_hash("src/app.py", "fn", "# comment\nx = 1")
        assert h1 == h2

    def test_different_file_paths_produce_different_hashes(self) -> None:
        h1 = generate_behavior_hash("src/a.py", "fn", "x = 1")
        h2 = generate_behavior_hash("src/b.py", "fn", "x = 1")
        assert h1 != h2

    def test_different_function_names_produce_different_hashes(self) -> None:
        h1 = generate_behavior_hash("src/a.py", "fn_a", "x = 1")
        h2 = generate_behavior_hash("src/a.py", "fn_b", "x = 1")
        assert h1 != h2

    def test_different_diffs_produce_different_hashes(self) -> None:
        h1 = generate_behavior_hash("src/app.py", "fn", "x = 1")
        h2 = generate_behavior_hash("src/app.py", "fn", "x = 2")
        assert h1 != h2

    def test_empty_function_name_allowed(self) -> None:
        h = generate_behavior_hash("src/app.py", "", "x = 1")
        assert len(h) == 64

    def test_js_inline_comment_ignored(self) -> None:
        h1 = generate_behavior_hash("app.js", "fn", "const x = 1")
        h2 = generate_behavior_hash("app.js", "fn", "const x = 1 // set x")
        assert h1 == h2

    def test_deterministic_across_calls(self) -> None:
        results = {generate_behavior_hash("f.py", "g", "return 1") for _ in range(5)}
        assert len(results) == 1


class TestHashMetadata:
    """Unit tests for hash_metadata."""

    def test_returns_64_char_hex_string(self) -> None:
        h = hash_metadata({"key": "value"})
        assert len(h) == 64

    def test_stable_across_insertion_order(self) -> None:
        h1 = hash_metadata({"a": "1", "b": "2"})
        h2 = hash_metadata({"b": "2", "a": "1"})
        assert h1 == h2

    def test_different_values_different_hash(self) -> None:
        h1 = hash_metadata({"key": "value1"})
        h2 = hash_metadata({"key": "value2"})
        assert h1 != h2

    def test_empty_dict(self) -> None:
        h = hash_metadata({})
        assert len(h) == 64
