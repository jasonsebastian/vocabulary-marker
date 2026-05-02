import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class ParseError(ValueError):
    pass


@dataclass
class Entry:
    display_word: str
    is_new: bool


def normalized_key(word: str) -> str:
    return word.strip().casefold()


def validate_word_not_reserved(word: str) -> None:
    if word.endswith(" n"):
        raise ValueError("word ending with ' n' is reserved")


def parse_output_line(raw_line: str, line_no: int) -> tuple[str, bool]:
    line = raw_line.rstrip("\n")
    if not line:
        raise ParseError(f"line {line_no}: blank line not allowed")
    if line.endswith(" n"):
        word = line[:-2]
        if not word:
            raise ParseError(f"line {line_no}: missing word before status")
        validate_word_not_reserved(word)
        return word, True
    validate_word_not_reserved(line)
    return line, False


def read_input_words(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    seen: set[str] = set()
    result: list[str] = []
    for raw in text.splitlines():
        word = raw.strip()
        if not word:
            continue
        validate_word_not_reserved(word)
        key = normalized_key(word)
        if key in seen:
            continue
        seen.add(key)
        result.append(word)
    return result


def read_output_entries(path: Path) -> dict[str, Entry]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    result: dict[str, Entry] = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        word, is_new = parse_output_line(raw, line_no)
        key = normalized_key(word)
        if key in result:
            raise ParseError(f"line {line_no}: duplicate normalized word '{key}'")
        result[key] = Entry(display_word=word, is_new=is_new)
    return result


def reconcile_entries(
    input_words: list[str],
    output_entries: dict[str, Entry],
    ask_status: Callable[[str], bool],
) -> tuple[list[Entry], dict[str, int]]:
    final_entries: list[Entry] = []
    seen_input_keys: set[str] = set()
    counts = {"kept": 0, "prompted": 0, "new": 0, "learnt": 0, "removed": 0}

    for word in input_words:
        key = normalized_key(word)
        seen_input_keys.add(key)
        if key in output_entries:
            entry = output_entries[key]
            final_entries.append(Entry(display_word=entry.display_word, is_new=entry.is_new))
            counts["kept"] += 1
            counts["new" if entry.is_new else "learnt"] += 1
            continue

        is_new = ask_status(word)
        final_entries.append(Entry(display_word=word, is_new=is_new))
        counts["prompted"] += 1
        counts["new" if is_new else "learnt"] += 1

    counts["removed"] = sum(1 for key in output_entries if key not in seen_input_keys)
    return final_entries, counts


def prompt_status(word_display: str) -> bool:
    while True:
        answer = input(f"{word_display} (type n if new, else Enter): ")
        if answer == "":
            return False
        if answer.lower() == "n":
            return True
        print("Invalid input. Type 'n' or press Enter.")


def render_output_lines(entries: list[Entry]) -> list[str]:
    sorted_entries = sorted(entries, key=lambda entry: normalized_key(entry.display_word))
    return [f"{entry.display_word} n" if entry.is_new else entry.display_word for entry in sorted_entries]


def write_output_atomic(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            for line in lines:
                temp_file.write(line + "\n")
        Path(temp_path).replace(path)
    finally:
        leftover = Path(temp_path)
        if leftover.exists():
            leftover.unlink()


def main() -> int:
    input_path = Path("input.txt")
    output_path = Path("output.txt")

    if not input_path.exists():
        print("input.txt not found")
        return 1

    try:
        input_words = read_input_words(input_path)
        output_entries = read_output_entries(output_path)
        final_entries, counts = reconcile_entries(input_words, output_entries, prompt_status)
        output_lines = render_output_lines(final_entries)
        write_output_atomic(output_path, output_lines)
    except (ParseError, ValueError, UnicodeDecodeError) as exc:
        print(str(exc))
        return 1
    except KeyboardInterrupt:
        print("Interrupted")
        return 1

    print("kept {kept}, prompted {prompted}, new {new}, learnt {learnt}, removed {removed}".format(**counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
