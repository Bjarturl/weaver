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
min_length = config.get("min_length", 1)
max_length = config.get("max_length", 100)
excluded_word_combinations = config.get("excluded_word_combinations", [])


def extract_ssn_standalone(personal_info):
    standalone_ssns = []
    import re

    for key, value in personal_info.items():
        if key.lower() == 'ssn' and value:
            value_str = str(value)
            numbers_in_text = re.findall(r'\d+', value_str)

            for num in numbers_in_text:
                if len(num) >= 9:
                    standalone_ssns.append(num)
                    standalone_ssns.append(num[-4:])
                else:
                    standalone_ssns.append(num)

    return standalone_ssns


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
                    if key.lower() != 'ssn':
                        extracted.append(value_str)

                numbers_in_text = re.findall(r'\d+', value_str)

                if key.lower() == 'ssn':
                    for num in numbers_in_text:
                        if len(num) >= 9:
                            extracted.append(num)
                            extracted.append(num[-4:])
                        else:
                            extracted.append(num)
                else:
                    extracted.extend(numbers_in_text)

    return [item for item in extracted if item and len(str(item)) > 0]


personal_data = extract_personal_data(personal_info)
standalone_ssns = extract_ssn_standalone(personal_info)

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
        combos.append(word)

        if has_digit:
            specials_only = [s for s in suffixes if all(
                not ch.isdigit() for ch in s)]
            for sc in specials_only:
                combos.append(word + sc)
        else:
            for num in numbers:
                combos.append(word + num)
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
                    for number in numbers:
                        for special in clean_special_chars:
                            password = pattern
                            if "{word}" in pattern:
                                password = password.replace(
                                    "{word}", word.lower())
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


def filter_passwords_by_length(passwords, min_length, max_length):
    return [p for p in passwords if min_length <= len(p) <= max_length]


def filter_excluded_combinations(passwords, excluded_combinations):
    if not excluded_combinations:
        return passwords

    filtered = []
    for password in passwords:
        password_lower = password.lower()
        excluded = False

        # Check if any two words from the excluded_combinations array appear together
        words_in_password = []
        for word in excluded_combinations:
            if word.lower() in password_lower:
                words_in_password.append(word.lower())

        # If 2 or more excluded words are found in the password, exclude it
        if len(words_in_password) >= 2:
            excluded = True

        if not excluded:
            filtered.append(password)

    return filtered


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
pattern_passwords = filter_passwords_by_length(
    pattern_passwords, min_length, max_length)
pattern_passwords = filter_excluded_combinations(
    pattern_passwords, excluded_word_combinations)

external_wordlist = load_external_wordlist(external_wordlist_file)

with open(output_file, "w") as f:
    for password in pattern_passwords:
        f.write(password + "\n")
    for ssn in standalone_ssns:
        f.write(ssn + "\n")
    for word in external_wordlist:
        f.write(word + "\n")

print(f"Generated {len(pattern_passwords)} from word patterns.")
print(f"Added {len(external_wordlist)} from external wordlist.")
print(
    f"Total written: {len(pattern_passwords) + len(standalone_ssns) + len(external_wordlist)}")
