# Vocabulary Marker CLI

Small Python CLI to mark words as learnt or new.

## What it does

- Reads words from `input.txt` (one word per line).
- Loads existing results from `output.txt` (if it exists).
- Skips words already present in `output.txt`.
- Prompts for unseen words:
  - Press `Enter` for learnt.
  - Type `n` for new.
- Removes entries from `output.txt` that are no longer in `input.txt`.
- Rewrites `output.txt` atomically and prints a run summary.

## Requirements

- Python 3.9+

## Usage

1. Create `input.txt` in project root:

```text
apple
banana
cherry
```

2. Run the CLI:

```bash
python3 main.py
```

Or use explicit command:

```bash
python3 main.py mark
```

3. Answer prompts like:

```text
apple (type n if new, else Enter):
```

4. Check `output.txt`.

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

## List new words

Run:

```bash
python3 main.py list-new
```

Output:

- Each new word on its own line.
- Final summary line: `total new: N`.

Example:

```text
Apple
Cherry
total new: 2
```

## Run tests

```bash
python3 -m unittest -v tests/test_main.py
```
