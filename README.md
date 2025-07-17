# 🔐 Password Wordlist Generator

A customizable password wordlist generator for red teamers and OSINT practitioners. Use personal and contextual data to build targeted password lists for ethical security testing.

## 🚀 Quick Start

1. **Setup**: Copy `config.example.json` → `config.json`
2. **Reset (optional)**: Run `python reset_config.py` to clear example data
3. **Edit config**: Fill in `config.json` with discovered personal info or desired keywords
4. **Generate**:
   ```bash
   python main.py
   ```
   Optional flags:
   - `--config <file>` — Use a custom config path
   - `--output <file>` — Save output to a custom file
   - `--external-wordlist <file>` — Merge with existing lists

## 🔧 Features

- Template-based password generation: `{word}`, `{number}`, `{special}`
- Recursively flattens data structures
- Converts dates like `YYYY-MM-DD` to multiple formats (`YYYY`, `YY`, `MMDD`, etc.)
- Icelandic accent normalization (`þ`, `ð`, `æ`)
- Case variants: lowercase, capitalized, UPPER
- Filters by length, uniqueness, exclusion rules
- Merges external wordlists (e.g., RockYou)

## 🧠 OSINT Collection Guide

Gather **actual word-like info** someone might use in a password:

### Social Media (Facebook, Instagram)

- **Names**: person, partner, child, pets
- **Hobbies**: Card/board game, sports teams, gamer handles, bands
- **Place names**: Boat, farm, town
- **Fandoms**: bands, games (e.g. "metallica", "zelda")
- **Dates**: weddings, birthdays, anniversaries
- **Cross-generational posts**: Grandparents often share family details like grandchildren's names in comments, or childhood pet names

**Where to find this info:**

- **Facebook/Instagram profiles**: Look for personal info, pet names, family members in posts and photos
- **Wedding photos**: Check descriptions and comments for date
- **Spouse details**: Cross-reference bios, tagged photos, and comments mentioning partners
- **Hobbies and interests**: Check photos or posts about activities, sports teams, favorite bands
- **Children's names**: Often mentioned in comments or posts by family members
- **Pet names**: Current and childhood pets visible in photo albums and stories
- **Historical content**: Old photo captions can reveal unique names like boat names, farm names, or childhood nicknames

### Professional (LinkedIn)

- **If you have only a username:**
  - If vague (e.g. admin), check if it's a tech platform and look for a developer or sysadmin at the company
  - On small sites, admin might map to one person
- **If the username is a first name:**
  - Search LinkedIn or company team pages to get full name
- **Find email format:**
  - Use `intext:"@target.is"` on Google to see how email addresses are structured for the company

### Iceland-Specific

- **Names**: Last names lead to parent names via friend list or likes/comments
- **Seasons + years**
- **Phone**: `ja.is` or Facebook
- **Kennitala + Address/Hometown**: Your heimabanki has a Þjóðskrá search by name.

## 🔑 Wordlist Strategy Tips

write about check if you can sign up to determine password rules

- Start simple: `{word}`, `{word}{number}`
- Expand complexity: `{word}{special}{word2}`, `{word}{number}{special}`
- Enable `all_cases` for capitalized/uppercase variants
- Set `generalize_strings` to `"both"` for full normalization
- Use `excluded_word_combinations` to avoid weak or meaningless combos
- Check company YouTube or software docs (if applicable) for admin login demos - note username and count password dots/asterisks to set exact `min_length`/`max_length`

## Security Notice

Use only with proper authorization. This tool is for ethical security testing and educational purposes only.
