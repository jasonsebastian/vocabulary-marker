import unittest
import io
import os
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from main import (
    Entry,
    ParseError,
    normalized_key,
    parse_output_line,
    main,
    read_input_words,
    read_output_entries,
    reconcile_entries,
    render_output_lines,
    prompt_status,
    write_output_atomic,
    validate_word_not_reserved,
)


class ParsingCoreTests(unittest.TestCase):
    def test_normalized_key_uses_trim_and_casefold(self) -> None:
        self.assertEqual(normalized_key("  Apple  "), "apple")

    def test_reserved_suffix_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_word_not_reserved("vitamin n")

    def test_parse_output_line_learnt(self) -> None:
        word, is_new = parse_output_line("Apple", 1)
        self.assertEqual(word, "Apple")
        self.assertFalse(is_new)

    def test_parse_output_line_new(self) -> None:
        word, is_new = parse_output_line("Apple n", 2)
        self.assertEqual(word, "Apple")
        self.assertTrue(is_new)

    def test_parse_output_line_blank_fails(self) -> None:
        with self.assertRaises(ParseError):
            parse_output_line("", 3)


class ReconcileTests(unittest.TestCase):
    def test_read_input_words_dedupes_case_insensitive(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "input.txt"
            path.write_text("Apple\napple\nBanana\n", encoding="utf-8")
            self.assertEqual(read_input_words(path), ["Apple", "Banana"])

    def test_read_output_entries_duplicate_key_fails(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "output.txt"
            path.write_text("Apple\napple n\n", encoding="utf-8")
            with self.assertRaises(ParseError):
                read_output_entries(path)

    def test_reconcile_keeps_existing_status_and_casing(self) -> None:
        input_words = ["apple", "Banana"]
        output_entries = {"apple": Entry(display_word="Apple", is_new=True)}
        asked: list[str] = []

        def ask_status(word: str) -> bool:
            asked.append(word)
            return False

        final_entries, counts = reconcile_entries(input_words, output_entries, ask_status)
        self.assertEqual(
            [(entry.display_word, entry.is_new) for entry in final_entries],
            [("Apple", True), ("Banana", False)],
        )
        self.assertEqual(asked, ["Banana"])
        self.assertEqual(counts["removed"], 0)

    def test_reconcile_removes_stale_output_entries(self) -> None:
        input_words = ["Apple"]
        output_entries = {
            "apple": Entry(display_word="Apple", is_new=False),
            "banana": Entry(display_word="Banana", is_new=True),
        }

        final_entries, counts = reconcile_entries(input_words, output_entries, lambda _word: False)
        self.assertEqual([entry.display_word for entry in final_entries], ["Apple"])
        self.assertEqual(counts["removed"], 1)


class InteractionAndWriteTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["x", "N"])
    def test_prompt_status_reprompts_until_valid(self, _mock_input) -> None:
        self.assertTrue(prompt_status("Apple"))

    def test_render_output_lines_sorts_by_normalized_key(self) -> None:
        lines = render_output_lines(
            [
                Entry(display_word="banana", is_new=False),
                Entry(display_word="Apple", is_new=True),
            ]
        )
        self.assertEqual(lines, ["Apple n", "banana"])

    def test_write_output_atomic_writes_expected_content(self) -> None:
        with TemporaryDirectory() as td:
            output_path = Path(td) / "output.txt"
            write_output_atomic(output_path, ["Apple n", "banana"])
            self.assertEqual(output_path.read_text(encoding="utf-8"), "Apple n\nbanana\n")


class MainIntegrationTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["", "n"])
    def test_main_reconciles_and_writes_sorted_output(self, _mock_input) -> None:
        with TemporaryDirectory() as td:
            cwd = Path(td)
            (cwd / "input.txt").write_text("Banana\nApple\nCherry\n", encoding="utf-8")
            (cwd / "output.txt").write_text("banana\n", encoding="utf-8")

            output_buffer = io.StringIO()
            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                with redirect_stdout(output_buffer):
                    code = main()
            finally:
                os.chdir(old_cwd)

            self.assertEqual(code, 0)
            self.assertEqual(
                (cwd / "output.txt").read_text(encoding="utf-8"),
                "Apple\nbanana\nCherry n\n",
            )
            self.assertIn("kept 1", output_buffer.getvalue())
            self.assertIn("prompted 2", output_buffer.getvalue())

    def test_main_missing_input_exits_nonzero(self) -> None:
        with TemporaryDirectory() as td:
            cwd = Path(td)
            output_buffer = io.StringIO()
            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                with redirect_stdout(output_buffer):
                    code = main()
            finally:
                os.chdir(old_cwd)

            self.assertEqual(code, 1)
            self.assertIn("input.txt not found", output_buffer.getvalue())


class ListNewCommandTests(unittest.TestCase):
    def test_list_new_prints_only_new_words_and_total(self) -> None:
        with TemporaryDirectory() as td:
            cwd = Path(td)
            (cwd / "output.txt").write_text("Apple n\nbanana\nCherry n\n", encoding="utf-8")
            output_buffer = io.StringIO()
            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                with redirect_stdout(output_buffer):
                    code = main(["list-new"])
            finally:
                os.chdir(old_cwd)

            self.assertEqual(code, 0)
            self.assertEqual(output_buffer.getvalue(), "Apple\nCherry\ntotal new: 2\n")

    def test_list_new_missing_output_prints_zero(self) -> None:
        with TemporaryDirectory() as td:
            cwd = Path(td)
            output_buffer = io.StringIO()
            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                with redirect_stdout(output_buffer):
                    code = main(["list-new"])
            finally:
                os.chdir(old_cwd)

            self.assertEqual(code, 0)
            self.assertEqual(output_buffer.getvalue(), "total new: 0\n")

    def test_list_new_malformed_output_fails_nonzero(self) -> None:
        with TemporaryDirectory() as td:
            cwd = Path(td)
            (cwd / "output.txt").write_text("\n", encoding="utf-8")
            output_buffer = io.StringIO()
            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                with redirect_stdout(output_buffer):
                    code = main(["list-new"])
            finally:
                os.chdir(old_cwd)

            self.assertEqual(code, 1)
            self.assertIn("blank line not allowed", output_buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
