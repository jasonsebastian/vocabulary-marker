# Vocabulary Marker CLI

Small Python CLI with two commands: `mark` and `list-new`.

## Table of contents

- [Commands](#commands)
- [What it does](#what-it-does)
- [File formats](#file-formats)
- [Rules and behavior](#rules-and-behavior)
- [Summary output](#summary-output)
- [Run tests](#run-tests)

## Commands

| Command | Purpose | Reads | Writes | Prompts |
| --- | --- | --- | --- | --- |
| `mark` | Mark unseen words as learnt/new and reconcile output | `input.txt`, `output.txt` | `output.txt` | Yes |
| `list-new` | Print words currently marked as new | `output.txt` | None | No |

Run commands:

```bash
python3 main.py          # default: mark
python3 main.py mark
python3 main.py list-new
```

`list-new` output examples:

Non-empty:

```text
Apple
Cherry
total new: 2
```

Zero results:

```text
total new: 0
```

## What it does

- `mark` reads `input.txt`, updates `output.txt`, and prompts for unseen words.
- `list-new` reads `output.txt` and prints only words marked new.
- `mark` loads existing results from `output.txt` (if it exists).
- `mark` skips words already present in `output.txt`.
- `mark` prompts for unseen words:
  - Press `Enter` for learnt.
  - Type `n` for new.
- `mark` removes entries from `output.txt` that are no longer in `input.txt`.
- `mark` rewrites `output.txt` atomically and prints a run summary.

## File formats

### `input.txt`

- One word per line.
- Leading/trailing spaces are trimmed.
- Blank lines are ignored.
- Duplicate words are deduplicated case-insensitively.
- Words ending with ` n` are rejected (reserved suffix).

### `output.txt`

Each line is either:

- `word` (learnt)
- `word n` (new)

Example:

```text
Apple
banana n
cherry
```

## Rules and behavior

- Matching is case-insensitive (`Apple` and `apple` are same word).
- Existing entries keep their current status and casing.
- New prompts follow `input.txt` order.
- Final `output.txt` is sorted alphabetically (case-insensitive).
- If `input.txt` is missing, program exits with error.
- If `output.txt` has malformed lines or duplicate normalized words, program exits with error.

## Summary output

At end of a successful run, CLI prints counts:

```text
kept X, prompted Y, new Z, learnt W, removed R
```

## Run tests

```bash
python3 -m unittest -v tests/test_main.py
```
