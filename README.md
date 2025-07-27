# Weaver

**Weaver** is a command-line wordlist generator for creating custom password lists from structured combinations of words, numbers, and special characters. It's built for password auditing, authorized penetration testing, and bug bounty workflows.

## Features

- Flexible DSL pattern syntax (`w`, `W`, `n`, `s`) for fast generation
- Case control with `--pattern-mode` (`as-is`, `cap`, `any`)
- Group exclusion logic (e.g., prevents `summer` and `winter` together)
- Min/max length filtering
- Supports `@file.txt` input for large custom wordlists
- Fast and lightweight for local use

## Command Line Options

### `--patterns PATTERNS` (Required)

Defines password structure using DSL symbols: `w`=word(lower), `W`=word(cap), `n/N`=number, `s/S`=special

```bash
--patterns 'WnS;Wn;wWn'  # Admin123!, Admin123, adminPassword123
```

### `--words WORDS`

Word groups separated by semicolons. Comma-separated words in same group won't appear together in a password.

```bash
--words 'admin,password;summer,winter'  # Groups prevent conflicts
--words @wordlist.txt                   # Load from file
```

### `--numbers NUMBERS`

Number groups like words. Comma-separated numbers in same group won't appear together.

```bash
--numbers '1978,1979;2020,2021,2023;0505'
--numbers @years.txt
```

### `--specials SPECIALS`

Special characters for passwords.

```bash
--specials '!@#$%'      # Each char separate
--specials '!,@;#,$'    # Grouped like words
--specials @symbols.txt
```

### `--words-file WORDS_FILE`

Single file with mixed content (words, numbers, specials). One item per line, comma-separated for groups.

### `--output OUTPUT` (Default: `wordlist.txt`)

Output file path.

### `--min-length MIN_LENGTH` (Default: `1`)

Minimum password length filter.

### `--max-length MAX_LENGTH` (Default: `100`)

Maximum password length filter.

### `--verbose`

Enable detailed logging with generation statistics.

### `--generalize` (Always enabled)

Unicode normalization is always enabled: `café` → `cafe`, `résumé` → `resume`

### `--pattern-mode {as-is,cap,any}` (Default: `as-is`)

- `as-is`: Use exact pattern casing (`W`=Cap, `w`=lower)
- `cap`: Both lowercase and capitalized
- `any`: lowercase, Capitalized, UPPERCASE

## Examples

### Basic Usage

```bash
# Simple wordlist
python weaver.py --patterns 'WnS;Wn' --words 'admin,password' --numbers '123,456' --specials '!@#'

# Personal target
python weaver.py --patterns 'Wn;WnS;WWn' --words 'jon,jonsson;snati,fyrirtaeki' --numbers '1978;2020,2023' --specials '_-#.!'

# File-based input
python weaver.py --patterns 'WnS' --words @names.txt --numbers @years.txt --output target.txt --min-length 8
```

### Advanced Examples

```bash
# Corporate passwords
python weaver.py --patterns 'W;Wn;WnS' --words 'admin,administrator;company,corp' --numbers '2024;123' --specials '!@#$' --min-length 8 --max-length 16

# OSINT-based targeting
python weaver.py --patterns 'WnS;WWn' --words 'target_name;company_name;@osint_words.txt' --numbers 'birth_year;@target_dates.txt' --specials '_-#.!@' --output osint_wordlist.txt --verbose
```

## Input Sources

### Personal Information (OSINT)

Effective passwords often use personal info: names, dates, places, interests, phone/address numbers.

### File Formats

```
# words.txt
admin
password
summer,winter,spring,autumn
jon,jonsson

# years.txt
2024
2023
1978

# symbols.txt
!
@
#
```

### Popular Wordlists

- [darknetehf Iceland lists](https://github.com/darknetehf/bug_bounty_tips/tree/main/password-lists/Iceland)
- [SecLists](https://github.com/danielmiessler/SecLists)
- Custom OSINT from social media/public records

## Usage with Tools

```bash
# WordPress login
ffuf -w wordlist.txt:FUZZ -X POST -d 'log=admin&pwd=FUZZ' -u https://target.com/wp-login.php -mc 302

# Basic Auth
ffuf -w wordlist.txt:FUZZ -u https://target.com/admin -H 'Authorization: Basic $(echo -n 'admin:FUZZ' | base64)'

# SSH brute force
hydra -l username -P wordlist.txt ssh://target.com

# API authentication
ffuf -w wordlist.txt:FUZZ -X POST -d '{'username':'admin','password':'FUZZ'}' -H 'Content-Type: application/json' -u https://api.target.com/login -mc 200
```

## Notes & Tips

- Output is automatically deduplicated and sorted
- Groups prevent conflicts (e.g., `summer` and `winter` together)
- Unicode normalization removes accents when `--generalize` is enabled
- Start with OSINT reconnaissance for targeted wordlists
- Use realistic patterns - people follow predictable password patterns
- Adjust length filters to match target password policies

## Quick Reference

| Parameter        | Required | Default        | Description                                           |
| ---------------- | -------- | -------------- | ----------------------------------------------------- |
| `--patterns`     | ✅       | None           | Password structure patterns (e.g., 'WnS;Ww')          |
| `--words`        | ❌       | Built-in list  | Word groups (semicolon/comma separated or @file)      |
| `--numbers`      | ❌       | Built-in list  | Number groups (semicolon/comma separated or @file)    |
| `--specials`     | ❌       | Built-in list  | Special chars (string, semicolon separated, or @file) |
| `--words-file`   | ❌       | None           | Single file with mixed content                        |
| `--output`       | ❌       | `wordlist.txt` | Output file path                                      |
| `--min-length`   | ❌       | `1`            | Minimum password length                               |
| `--max-length`   | ❌       | `100`          | Maximum password length                               |
| `--verbose`      | ❌       | `false`        | Enable detailed logging                               |
| `--generalize`   | ❌       | `always on`    | Unicode normalization (always enabled)                |
| `--pattern-mode` | ❌       | `as-is`        | Case handling: `as-is`, `cap`, `any`                  |

**Pattern Symbols:** `w`=word(lower), `W`=word(cap), `n/N`=number, `s/S`=special

**Common Patterns:** `WnS`, `Wn`, `wn`, `nnn`, `WWn`, `wsn`

## Ethical Use

This tool is intended for **authorized testing** and **educational purposes** only. Always get proper consent before using this for any kind of password testing, enumeration, or brute force work.

## License

MIT
