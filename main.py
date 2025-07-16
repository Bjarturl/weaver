import itertools
import json

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

common_words = config["common_words"]
common_numbers = config["common_numbers"]
common_special_chars = config["common_special_chars"]

custom_words = config["custom"]["words"]
custom_numbers = config["custom"]["numbers"]
personal_info = config["custom"]["personal_info"]

external_wordlist_file = config["external_wordlist"]
output_file = config["output_file"]
word_patterns = config["word_patterns"]
all_cases = config.get("all_cases", False)


def extract_personal_data(personal_info):
    extracted = []
    import re

    for key, value in personal_info.items():
        if not value:
            continue

        if isinstance(value, list):
            for item in value:
                if item:
                    extracted.append(str(item).lower())
        else:
            value_str = str(value).lower()

            if re.match(r'\d{4}-\d{2}-\d{2}', value_str):
                parts = value_str.split('-')
                year, month, day = parts[0], parts[1], parts[2]
                extracted.extend(
                    [year, year[-2:], month, day, month + day, day + month])
            else:
                if ' ' in value_str:
                    for word in value_str.split():
                        if word and len(word) > 1:
                            extracted.append(word.lower())
                else:
                    extracted.append(value_str)

                numbers_in_text = re.findall(r'\d+', value_str)

                # Special handling for SSN-like patterns (9+ digits)
                for num in numbers_in_text:
                    if len(num) >= 9:
                        extracted.append(num)  # Full SSN as standalone entry
                        extracted.append(num[-4:])  # Last 4 digits
                    else:
                        extracted.append(num)

                # Also check if the entire value is a standalone SSN (without text)
                if value_str.isdigit() and len(value_str) >= 9:
                    extracted.append(value_str)  # Full SSN standalone
                    extracted.append(value_str[-4:])  # Last 4 digits

    return [item for item in extracted if item and len(str(item)) > 0]


# Extract personal data and combine with custom data
personal_data = extract_personal_data(personal_info)

# Separate personal data into words and numbers
personal_words = []
personal_numbers = []

for item in personal_data:
    item_str = str(item)
    if item_str.isdigit():
        personal_numbers.append(item_str)
    else:
        personal_words.append(item_str)

# Combine words and numbers separately
all_words = common_words + custom_words + personal_words
all_numbers = common_numbers + custom_numbers + personal_numbers


def capitalize_first(s):
    return s[0].upper() + s[1:] if s else s


def generate_base_words(words, numbers):
    base_words = set()

    for w in words:
        base_words.add(capitalize_first(w))
        base_words.add(w.lower())

    for w1, w2 in itertools.permutations(words, 2):
        w1_cap = capitalize_first(w1)
        w2_cap = capitalize_first(w2)
        w1_low = w1.lower()
        w2_low = w2.lower()

        base_words.add(w1_cap + w2_cap)
        base_words.add(w1_low + w2_low)

        for n in numbers:
            base_words.add(w1_cap + n + w2_cap)
            base_words.add(w1_low + n + w2_low)

    return list(base_words)


def generate_suffixes(numbers, special_chars):
    suffixes = set()
    for n in numbers:
        suffixes.add(n)
    for s in special_chars:
        suffixes.add(s)
    for n in numbers:
        for s in special_chars:
            suffixes.add(n + s)
            suffixes.add(s + n)
    return list(suffixes)


def generate_combo_wordlist(base_words, numbers, suffixes):
    combos = []
    for word in base_words:
        has_digit = any(c.isdigit() for c in word)
        combos.append(word)  # Always include base

        if has_digit:
            # Only add special chars
            specials_only = [s for s in suffixes if all(
                not ch.isdigit() for ch in s)]
            for sc in specials_only:
                combos.append(word + sc)
        else:
            # Add number-only suffixes first
            for num in numbers:
                combos.append(word + num)
            # Then full suffixes (number + special)
            for suffix in suffixes:
                combos.append(word + suffix)
    return combos


def generate_pattern_passwords(patterns, words, numbers, special_chars):
    passwords = set()
    clean_special_chars = [
        s for s in special_chars if not any(c.isdigit() for c in s)]

    for pattern in patterns:
        has_word2 = "{word2}" in pattern or "{Word2}" in pattern
        has_word3 = "{word3}" in pattern or "{Word3}" in pattern
        has_number = "{number}" in pattern
        has_special = "{special}" in pattern

        if not has_word2 and not has_word3:
            for word in words:
                word_has_number = any(c.isdigit() for c in word)

                if has_number and has_special:
                    for i, number in enumerate(numbers):
                        special = clean_special_chars[i % len(
                            clean_special_chars)] if clean_special_chars else ""
                        password = pattern
                        if "{word}" in pattern:
                            password = password.replace("{word}", word.lower())
                        if "{Word}" in pattern:
                            password = password.replace(
                                "{Word}", capitalize_first(word))

                        if not word_has_number:
                            password = password.replace("{number}", number)
                        else:
                            password = password.replace("{number}", "")

                        password = password.replace("{special}", special)
                        passwords.add(password)
                elif has_number:
                    if not word_has_number:
                        for number in numbers:
                            password = pattern
                            if "{word}" in pattern:
                                password = password.replace(
                                    "{word}", word.lower())
                            if "{Word}" in pattern:
                                password = password.replace(
                                    "{Word}", capitalize_first(word))
                            password = password.replace("{number}", number)
                            passwords.add(password)
                elif has_special:
                    for special in clean_special_chars:
                        password = pattern
                        if "{word}" in pattern:
                            password = password.replace("{word}", word.lower())
                        if "{Word}" in pattern:
                            password = password.replace(
                                "{Word}", capitalize_first(word))
                        password = password.replace("{special}", special)
                        passwords.add(password)
                else:
                    password = pattern
                    if "{word}" in pattern:
                        password = password.replace("{word}", word.lower())
                    if "{Word}" in pattern:
                        password = password.replace(
                            "{Word}", capitalize_first(word))
                    passwords.add(password)

        elif not has_word3:
            for word in words:
                for word2 in words:
                    if word == word2:
                        continue

                    password = pattern
                    if "{word}" in pattern:
                        password = password.replace("{word}", word.lower())
                    if "{Word}" in pattern:
                        password = password.replace(
                            "{Word}", capitalize_first(word))
                    if "{word1}" in pattern:
                        password = password.replace("{word1}", word.lower())
                    if "{word2}" in pattern:
                        password = password.replace("{word2}", word2.lower())
                    if "{Word1}" in pattern:
                        password = password.replace(
                            "{Word1}", capitalize_first(word))
                    if "{Word2}" in pattern:
                        password = password.replace(
                            "{Word2}", capitalize_first(word2))

                    words_have_numbers = any(c.isdigit() for c in word + word2)

                    if has_number and has_special:
                        if not words_have_numbers:
                            for number in numbers:
                                for special in clean_special_chars:
                                    temp_password = password
                                    temp_password = temp_password.replace(
                                        "{number}", number)
                                    temp_password = temp_password.replace(
                                        "{special}", special)
                                    passwords.add(temp_password)
                        else:
                            for special in clean_special_chars:
                                temp_password = password
                                temp_password = temp_password.replace(
                                    "{number}", "")
                                temp_password = temp_password.replace(
                                    "{special}", special)
                                passwords.add(temp_password)
                    elif has_number and not words_have_numbers:
                        for number in numbers:
                            temp_password = password
                            temp_password = temp_password.replace(
                                "{number}", number)
                            passwords.add(temp_password)
                    elif has_special:
                        for special in clean_special_chars:
                            temp_password = password
                            temp_password = temp_password.replace(
                                "{special}", special)
                            passwords.add(temp_password)
                    else:
                        passwords.add(password)

        else:
            for i, word in enumerate(words[:3]):
                for j, word2 in enumerate(words[:3]):
                    if word == word2:
                        continue
                    for k, word3 in enumerate(words[:3]):
                        if word3 == word or word3 == word2:
                            continue

                        password = pattern
                        if "{word}" in pattern:
                            password = password.replace("{word}", word.lower())
                        if "{Word}" in pattern:
                            password = password.replace(
                                "{Word}", capitalize_first(word))
                        if "{word1}" in pattern:
                            password = password.replace(
                                "{word1}", word.lower())
                        if "{word2}" in pattern:
                            password = password.replace(
                                "{word2}", word2.lower())
                        if "{word3}" in pattern:
                            password = password.replace(
                                "{word3}", word3.lower())
                        if "{Word1}" in pattern:
                            password = password.replace(
                                "{Word1}", capitalize_first(word))
                        if "{Word2}" in pattern:
                            password = password.replace(
                                "{Word2}", capitalize_first(word2))
                        if "{Word3}" in pattern:
                            password = password.replace(
                                "{Word3}", capitalize_first(word3))

                        words_have_numbers = any(c.isdigit()
                                                 for c in word + word2 + word3)

                        if has_number and has_special:
                            if not words_have_numbers:
                                for number in numbers:
                                    for special in clean_special_chars:
                                        temp_password = password
                                        temp_password = temp_password.replace(
                                            "{number}", number)
                                        temp_password = temp_password.replace(
                                            "{special}", special)
                                        passwords.add(temp_password)
                            else:
                                for special in clean_special_chars:
                                    temp_password = password
                                    temp_password = temp_password.replace(
                                        "{number}", "")
                                    temp_password = temp_password.replace(
                                        "{special}", special)
                                    passwords.add(temp_password)
                        elif has_number and not words_have_numbers:
                            for number in numbers:
                                temp_password = password
                                temp_password = temp_password.replace(
                                    "{number}", number)
                                passwords.add(temp_password)
                        elif has_special:
                            for special in clean_special_chars:
                                temp_password = password
                                temp_password = temp_password.replace(
                                    "{special}", special)
                                passwords.add(temp_password)
                        else:
                            passwords.add(password)

    return list(passwords)


def load_external_wordlist(filename):
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(
            f"Warning: External wordlist file '{filename}' not found. Skipping external wordlist.")
        return []


def has_multiple_numeric_substrings(password):
    import re
    numeric_parts = re.findall(r'\d+', password)
    return len(numeric_parts) > 1


def filter_passwords_with_multiple_numbers(passwords):
    return [p for p in passwords if not has_multiple_numeric_substrings(p)]


def expand_patterns_for_all_cases(patterns, all_cases):
    if not all_cases:
        return patterns

    expanded = []
    for pattern in patterns:
        expanded.append(pattern)

        capitalized_pattern = pattern
        capitalized_pattern = capitalized_pattern.replace("{word}", "{Word}")
        capitalized_pattern = capitalized_pattern.replace("{word1}", "{Word1}")
        capitalized_pattern = capitalized_pattern.replace("{word2}", "{Word2}")
        capitalized_pattern = capitalized_pattern.replace("{word3}", "{Word3}")

        if capitalized_pattern != pattern:
            expanded.append(capitalized_pattern)

    return expanded


personal_data = extract_personal_data(personal_info)

personal_words = []
personal_numbers = []

for item in personal_data:
    item_str = str(item)
    if item_str.isdigit():
        personal_numbers.append(item_str)
    else:
        personal_words.append(item_str)

all_words = common_words + custom_words + personal_words
all_numbers = common_numbers + custom_numbers + personal_numbers

expanded_patterns = expand_patterns_for_all_cases(word_patterns, all_cases)

clean_special_chars = [
    s for s in common_special_chars if not any(c.isdigit() for c in s)]
suffixes = generate_suffixes(all_numbers, clean_special_chars)


def estimate_password_count(patterns, words, numbers, special_chars):
    total = 0
    for pattern in patterns:
        has_word2 = "{word2}" in pattern or "{Word2}" in pattern
        has_word3 = "{word3}" in pattern or "{Word3}" in pattern
        has_number = "{number}" in pattern
        has_special = "{special}" in pattern

        if not has_word2 and not has_word3:
            word_count = len(words)
            if has_number and has_special:
                total += word_count * len(numbers)
            elif has_number:
                total += word_count * len(numbers)
            elif has_special:
                total += word_count * len(special_chars)
            else:
                total += word_count
        elif not has_word3:
            word_count = len(words) * (len(words) - 1)
            if has_number and has_special:
                total += word_count * len(numbers) * len(special_chars)
            elif has_number:
                total += word_count * len(numbers)
            elif has_special:
                total += word_count * len(special_chars)
            else:
                total += word_count
        else:
            word_count = 3 * 2 * 1
            if has_number and has_special:
                total += word_count * len(numbers) * len(special_chars)
            elif has_number:
                total += word_count * len(numbers)
            elif has_special:
                total += word_count * len(special_chars)
            else:
                total += word_count
    return total


estimated_count = estimate_password_count(
    expanded_patterns, all_words, all_numbers, clean_special_chars)

if estimated_count > 10_000_000:
    print(f"WARNING: About to generate {estimated_count:,} passwords!")
    print("This is over 10 million passwords and may take a long time and use significant disk space.")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted.")
        exit()

pattern_passwords = generate_pattern_passwords(
    expanded_patterns, all_words, all_numbers, clean_special_chars)

pattern_passwords = filter_passwords_with_multiple_numbers(pattern_passwords)

external_wordlist = load_external_wordlist(external_wordlist_file)

with open(output_file, "w") as f:
    for password in pattern_passwords:
        f.write(password + "\n")
    for word in external_wordlist:
        f.write(word + "\n")

print(f"Generated {len(pattern_passwords)} from word patterns.")
print(f"Added {len(external_wordlist)} from external wordlist.")
print(f"Total written: {len(pattern_passwords) + len(external_wordlist)}")
