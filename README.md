# Password Wordlist Generator

A flexible, config-driven tool for building targeted password lists from patterns, personal data, and common password elements.

- **No code changes needed**  
  Everything lives in `config.json`: words, numbers, specials, patterns, filters.

- **Free-form custom data**  
  Under the top-level `"custom"` section you can add **any** keys—arrays or values of names, nicknames, dates, IDs, hobbies, whatever. The generator will recursively pick up every string or number, extract words, dates (YYYY-MM-DD → parts), and all digit-groups automatically.

  > _Note_: using a `"personal_info"` object is just a common convention, not a requirement.

- **Dynamic patterns**  
  Use `{word}`, `{word2}`, `{WORD3}`, `{number}`, `{special}` in your patterns.  
  Placeholders are parsed at runtime, so you can add as many as you like.

- **Built-in filters**

  - Length (`min_length` / `max_length`)
  - Single numeric substring (avoid multiple number blocks)
  - Exclusions: any password containing any pair from any exclusion group in `excluded_word_combinations` is dropped.

- **String processing options**

  - `all_cases`: If `true`, automatically generates capitalized versions of `{word}` patterns (e.g., `{word}` → `{Word}`)
  - `generalize_strings`: Controls accent/special character removal from extracted words
    - `true` (default): Replace accented characters with ASCII equivalents (e.g., "grágás" → "gragas")
    - `false`: Keep original characters as-is
    - `"both"`: Include both original and generalized versions

- **External lists**  
  Append a raw wordlist via `external_wordlist` — no pattern filling applied.

- **CLI options**
  ```bash
  python main.py [--config other.json] [--output list.txt] [--verbose]
  ```

## Quick Start

1. Copy `config.example.json` → `config.json`.
2. Tweak words, numbers, specials, patterns, filters.
3. Under `"custom"`, add **any** fields — pick the key names to be convenient for you to fill out.
4. Run:
   ```bash
   python main.py
   ```
5. Your wordlist lands in `wordlist.txt` (or your chosen `output_file`).

## Configuration Options

### Core Settings

- `output_file`: Name of the generated wordlist file
- `external_wordlist`: Path to an external wordlist to append (optional)
- `min_length` / `max_length`: Password length constraints

### Processing Options

- `all_cases`: If `true`, automatically generates capitalized versions of `{word}` patterns
- `generalize_strings`: Controls accent/special character removal from extracted words
  - `true` (default): Replace accented characters with ASCII equivalents
  - `false`: Keep original characters as-is
  - `"both"`: Include both original and generalized versions

### Word Sources

- `common_words`: List of common words to use in patterns
- `common_numbers`: List of common numbers to use in patterns
- `common_special_chars`: List of special characters to use in patterns
- `custom`: Nested object containing personal data (any structure allowed)

### Pattern Generation

- `word_patterns`: List of patterns using placeholders like `{word}`, `{number}`, `{special}`
- `excluded_word_combinations`: List of word groups - passwords containing any pair from the same group will be excluded

## Custom Data Extraction

Every value under the `"custom"` section is processed—no fixed key names required:

```json
"custom": {
  "personal_info": {
    "full_name": "Jane Doe",
    "pets": ["fido", "milo"]
  },
  "hobbies": ["skiing", "gaming"],
  "national_id": "0123456789"
}
```

- **Words**: split on spaces, lowercased, optionally generalized (accents removed)
- **Dates**: `YYYY-MM-DD` → `YYYY`, `YY`, `MM`, `DD`, `MMDD`, `DDMM`
- **Numbers**: any digit groups

## Resetting Your Config

To clear out **all** custom entries (regardless of key names):

```bash
python reset_config.py
```

## Security and Legal Notice

**This tool is for authorized security testing and educational purposes only.**

- Ensure you have proper written authorization before testing any target
- Only use on systems you own or have explicit permission to test
- Follow all applicable laws and regulations in your jurisdiction
- This tool should not be used for malicious purposes
