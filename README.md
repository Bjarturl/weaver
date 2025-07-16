# Password Generator

A configurable password generator that creates targeted wordlists based on personal information and common patterns. This tool helps security professionals generate realistic password lists for testing and assessment purposes.

## Features

- **Personal Information Extraction**: Automatically extracts components from names, SSNs, dates, and other personal data
- **Configurable Patterns**: Define custom password patterns using placeholders
- **External Wordlist Integration**: Combine with existing wordlists (e.g., rockyou.txt) - used as-is without modification
- **Common Password Patterns**: Includes real-world password patterns people actually use
- **Case Sensitivity Control**: `all_cases` flag to automatically generate both lowercase and capitalized versions

## Configuration

Rename `config.example.json` to `config.json`. Customize:

```json
{
  "common_words": ["admin", "password"],
  "common_numbers": ["123", "2024", "69"],
  "common_special_chars": ["!", "@", "#", "$"],
  "custom": {
    "words": ["company", "department"],
    "numbers": ["1234567"],
    "personal_info": {
      "name": "John Smith",
      "birth_date": "1985-03-22",
      "pet_names": ["buddy", "max"],
      "whatever": "Springfield",
      ...
    }
  },
  "external_wordlist": "leaked.txt",
  "all_cases": true,
  "word_patterns": [
    "{word}",
    "{word}{number}",
    "{word}{word2}",
    "{word}{special}{word2}",
    "{word}{word2}{number}",
    "{word}{word2}{number}{special}"
  ]
}
```

**Key Points:**

- **Personal info keys don't matter** - Use any field names you want (`name`, `hometown`, `pet`, etc.)
- **All text is extracted** - Names split into words, numbers extracted, dates parsed
- **Arrays supported** - `["pet1", "pet2"]` works for multiple values
- **`all_cases: true`** - Automatically generates both `admin` and `Admin` from `{word}` patterns
- **External wordlist** - Added as-is (no pattern processing)

## Personal Information Gathering (OSINT)

**Icelandic Resources:**

- **[ja.is](https://ja.is)** - Phone directory, addresses, personal information
- Your heimabanki - SSN lookup by name

**General Sources:**

- **Social Media** - Facebook, LinkedIn, Instagram, Twitter/X
- **Google Search** - "name + city" or "name + company"
- **Public Directories** - Phone numbers, addresses

**What to Look For:**

- Names, nicknames, family members
- Birth dates, anniversaries, significant years
- Locations, addresses, hometown
- Sports teams, hobbies, interests
- Pet names, company names
- Phone numbers, partial SSNs

## WordPress Username Enumeration

**REST API Method:**

```
https://target.com/wp-json/wp/v2/users
https://target.com?rest_route=wp/v2/users
```

**Author Archive URLs:**

```
https://target.com/?author=0
https://target.com/?author=1
https://target.com/author/username
```

**Login Error Messages:**

- Try common usernames on `/wp-login.php`
- Different error messages reveal if username exists

**Tools:**

- **wpscan**: `wpscan --url https://target.com --enumerate u`

**Common WordPress Usernames:**

- `admin`, `administrator`, `root`
- `wp-admin`, `webmaster`, `user`
- Site name variations
- Author names from posts/pages

## Usage

1. Gather target information using OSINT
2. Add info to `config.json` e.g. under `personal_info` or `custom`.
3. Run: `python main.py`
4. Generated passwords saved to specified output file

## Security and Legal Notice

**This tool is for authorized security testing and educational purposes only.**

- Ensure you have proper written authorization before testing any target
- Only use on systems you own or have explicit permission to test
- Follow all applicable laws and regulations in your jurisdiction
- This tool should not be used for malicious purposes

## Use Cases

- WordPress penetration testing
- Bug bounty hunting
- Security assessments
- Authorized penetration testing
