# Password Generator README

This password generator produces targeted wordlists by combining configurable patterns, personal data, and common password elements. It’s designed to be:

- **Flexible**: Supports any number of `{wordX}`, `{number}`, and `{special}` placeholders with automatic case handling.
- **Config-Driven**: All input comes from a single `config.json`; no code changes needed for new patterns or data.
- **Efficient**: Generates combinations in a unified loop and filters duplicates, multi-digit substrings, and unwanted combinations in one pass.

## Core Concepts and Design Decisions

### 1. Dynamic Placeholder Parsing

- Patterns can include any number of word tokens (`{word}`, `{word2}`, `{WORD3}`, etc.), plus `{number}` and `{special}`.
- The code extracts placeholder names and their intended case (lower, capitalize, upper) at runtime.
- This avoids hard-coding support for a fixed number of words and makes the engine future-proof.

### 2. Single-Pass Combination Generation

- All token pools (words, numbers, specials) are determined per pattern.
- `itertools.product` generates every cross-combination in one unified loop, simplifying logic and ensuring consistency.
- Passwords are collected into a `set` to remove duplicates immediately.

### 3. Unified Filtering

- Post-generation, each candidate goes through a concise filter that enforces:

  - **Length bounds** (`min_length` / `max_length`).
  - **Single numeric substring** (to avoid overly complex numeric patterns).
  - **Excluded-word logic**: Any candidate containing two or more entries from `excluded_word_combinations` is dropped.

- This keeps the wordlist focused and avoids manual pruning later.

### 4. Config-First Approach

- All parameterization lives in **one** `config.json`.
- No code edits required for new words, numbers, specials, patterns, or filters.
- Supports an **external wordlist** file, appended raw at the end.

### 5. CLI Ergonomics

- **`--config`**: specify an alternate config file.
- **`--output`**: override the target output filename.
- **`--verbose`**: switch on debug-level logging for troubleshooting.
- Non-interactive design: no prompts or pauses; suitable for automation and CI/CD pipelines.

## Installation and Setup

1. **Clone or download** this repository.
2. Copy `config.example.json` to `config.json`.
3. Install Python (3.7+ recommended).

## Configuration (`config.json`)

```json
{
  "common_words": ["admin", "password", "Vor", "Sumar"],
  "common_numbers": ["123", "2024", "321", "1"],
  "common_special_chars": ["!", "?", "#", "$", "."],
  "custom": {
    "words": ["company", "dept"],
    "numbers": ["8675309"],
    "personal_info": {
      "name": "Jane Doe",
      "birth_date": "1990-07-15",
      "pet_names": ["fido", "milo"],
      "ssn": ""
    }
  },
  "external_wordlist": "rockyou.txt",
  "all_cases": true,
  "min_length": 6,
  "max_length": 14,
  "excluded_word_combinations": ["sumar", "vetur", "haust", "vor"],
  "word_patterns": [
    "{word}",
    "{word}{number}",
    "{word}{special}{word2}",
    "{number}{word2}",
    "{word}{word2}{number}{special}"
  ],
  "output_file": "wordlist.txt"
}
```

- **Placeholders**: any `{wordX}`, `{number}`, and `{special}` maps to its respective pool.
- **`all_cases`**: duplicates patterns replacing `{word}` with `{Word}` for capitalized variants.
- **`excluded_word_combinations`**: any password containing two or more of these substrings (case-insensitive) will be dropped.

## Running the Generator

```bash
# Default config.json → wordlist.txt
python main.py

# Alternate config and output path
python main.py --config myconfig.json --output custom-list.txt

# Verbose logging
python main.py --verbose
```

## Tips and Best Practices

- **Pattern Design**: Keep patterns to the essential ones you need; avoid overly generic patterns unless necessary.
- **Personal Data**: Use relevant personal info fields (names, dates, nicknames) but avoid leaving empty fields in the list if they’re unused.
- **External Lists**: Append large, static lists (e.g., rockyou) with `external_wordlist`—pattern parsing is not applied to those entries.
- **Filtering**: Tune `min_length`/`max_length` and exclusions to fit your targeting scope and policy constraints.

## Security and Legal Notice

**This tool is for authorized security testing and educational purposes only.**

- Ensure you have proper written authorization before testing any target
- Only use on systems you own or have explicit permission to test
- Follow all applicable laws and regulations in your jurisdiction
- This tool should not be used for malicious purposes
