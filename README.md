# Password Wordlist Generator

A simple, config-driven tool to build custom password lists from personal data, common words, and patterns.

## Features

- **Config-only**: Define everything in `config.json` — no code edits needed.
- **Auto extraction**: Recursively pulls strings, dates (`YYYY-MM-DD` → parts), numbers, and digit-groups from any nested fields under `words`.
- **Flexible patterns**: Use `{word}`, `{word2}`, `{WORD3}`, `{number}`, `{special}`. Unlimited placeholders and case variants.
- **Powerful filters**:

  - Length (`min_length`, `max_length`)
  - Single numeric block (drops multiple number groups)
  - Exclusions (drops passwords containing any two items from the same exclusion group)

- **Accent handling**: Strips or preserves accents based on `generalize_strings` (`true`, `false`, or `"both"`).
- **Case options**: `all_cases: true` auto-adds capitalized `{Word}` variants.
- **External lists**: Append raw wordlists via `--external-wordlist`.

## Quick Start

1. Copy `config.example.json` → `config.json`.
2. Fill in `words` (any structure: `personal_info`, `hobbies`, etc.).
3. Adjust `word_patterns`, `min_length`, `max_length`, and `excluded_word_combinations`.
4. Run:

   ```bash
   python main.py [--config other.json] [--output list.txt] [--external-wordlist rockyou.txt] [--verbose]
   ```

5. Find your list in `wordlist.txt` (or your specified `output_file`).

## Configuration Example

```json
{
  "output_file": "wordlist.txt",
  "min_length": 6,
  "max_length": 12,
  "generalize_strings": true,
  "all_cases": false,
  "words": {
    "personal_info": { "name": "Jane Doe", "pets": ["fido", "milo"] },
    "common_words": ["admin", "password"],
    "common_numbers": ["123", "2024"]
  },
  "word_patterns": ["{word}{number}", "{Word}{special}{word2}"],
  "excluded_word_combinations": [
    ["admin", "administrator"],
    ["spring", "summer", "autumn", "winter"]
  ]
}
```

## Key Fields

- **words**: Any nested data; all strings/numbers processed.
- **word_patterns**: Placeholder list.
- **excluded_word_combinations**: Lists of items — any two in a password triggers exclusion. See `config.example.json` for examples.
- **generalize_strings**: `true`, `false`, or `"both"`.
- **all_cases**: `true` to auto-add capitalized patterns.

## Tips & Tricks

- **Start simple**: Begin with `{word}` and `{word}{number}` patterns.
- **Add complexity gradually**: Incorporate specials and multiple words (e.g., `{word}{special}{word2}`).
- **Use case variants**: Enable `all_cases` to capture uppercase and capitalized forms.
- **Leverage both accents**: Set `generalize_strings` to `"both"` for original and accent-free words. Non accented letters are more likely though as some websites may forbid those and users have gotten used to having passwords like that.
- **Align with real-world formats**: If you spot a date format (e.g., birthdays), include it under `words` as `YYYY-MM-DD` to auto-split.
- **Password rules**: If you can register, note which password rules are required and configure the word patterns based on that.
- **Combine external lists**: Use `--external-wordlist rockyou.txt` for broader coverage when personal data is limited.

### OSINT Techniques

#### Social Media Research

- Facebook/Instagram profiles: personal info, pet names, family members.
- Wedding photos: descriptions or comments for dates, locations, or names.
- Spouse details: bios, tagged photos, comments mentioning a partner.
- Hobbies: check photos or posts of common activities.
- Children’s names: comments or posts by family.
- Pet names: current and childhood pets in albums.
- Historical content: captions on old photos for unique names or locations like boat/farm names.

#### Professional Research

- Company websites: staff directories, team pages, about sections.
- LinkedIn: connections, job history, skills.
- Username correlation: cross-reference usernames with company social media or directories.
- Username enumeration: check login error differences to confirm account existence.
- Google: Google the person's name if not too generic.
- Demo recordings: check documentation, YouTube/Vimeo demos for login screenshots—note usernames and password length to adjust `min_length`/`max_length`.

#### Iceland-Specific Research

- Kennitala lookups: use services like íslendingabók or your heimabanki to find birth dates.
- Phone numbers: search on ja.is.
- Patronymic naming: for `-son`/`-dóttir`, search for likely parents in comments or likes.
- Cross-generational posts: grandparents often share family details like children's names.

#### Cultural & Seasonal Patterns

- Seasonal words: `vor` (spring), `sumar` (summer), `haust` (autumn), `vetur` (winter).
- Recent years: `2025`, `2024`, `2023`

## Security Notice

Use only with proper authorization. This tool is for ethical security testing and educational purposes only.
