#!/usr/bin/env python3
import argparse
import itertools
import json
import logging
import re
import unicodedata


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generalize_string(s):
    """Remove accents and special characters from a string, including Icelandic characters."""
    # Handle special Icelandic characters first
    replacements = {
        'ð': 'd', 'Ð': 'D',
        'þ': 'th', 'Þ': 'Th',
        'æ': 'ae', 'Æ': 'Ae',
        'ø': 'o', 'Ø': 'O'
    }

    result = s
    for old, new in replacements.items():
        result = result.replace(old, new)

    # Normalize to NFD (decomposed form) and remove combining characters
    normalized = unicodedata.normalize('NFD', result)
    # Remove combining characters (accents)
    ascii_string = ''.join(
        c for c in normalized if unicodedata.category(c) != 'Mn')
    return ascii_string


def flatten_values(obj):
    """Recursively yield all atomic values (str, int, float) from nested dicts/lists."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from flatten_values(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten_values(item)
    elif isinstance(obj, (str, int, float)):
        yield obj


def extract_personal_data(values, generalize_strings=True):
    """
    From a list of raw values, extract:
      - lowercase words (splitting on spaces, skipping single letters)
      - dates YYYY-MM-DD → components (YYYY, YY, MM, DD, MMDD, DDMM)
      - all numeric substrings

    If generalize_strings is True, also create generalized versions of words.
    If generalize_strings is "both", include both original and generalized versions.
    """
    items = []
    for raw in values:
        s = str(raw).lower()
        # date parts
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            y, m, d = s.split('-')
            items += [y, y[-2:], m, d, m + d, d + m]
        else:
            # words
            for w in s.split():
                if len(w) > 1 and not w.isdigit():
                    items.append(w)
                    # Add generalized version if requested
                    if generalize_strings:
                        generalized = generalize_string(w)
                        if generalized != w:
                            if generalize_strings == "both":
                                items.append(generalized)
                            else:
                                # Replace the original with generalized
                                items[-1] = generalized
        # all numbers
        items += re.findall(r"\d+", s)
    return items


def parse_placeholders(pattern):
    tokens = []
    for m in re.finditer(r"\{(.*?)\}", pattern):
        name = m.group(1)
        if re.match(r'(?i)word\d*$', name):
            case = (
                'upper' if name.isupper()
                else 'capitalize' if name[0].isupper()
                else 'lower'
            )
            tokens.append((name, 'word', case))
        elif name == 'number':
            tokens.append((name, 'number', None))
        elif name == 'special':
            tokens.append((name, 'special', None))
    return tokens


def fill_pattern(pattern, tokens, values):
    out = pattern
    for (name, kind, case), val in zip(tokens, values):
        if kind == 'word':
            if case == 'upper':
                val = val.upper()
            elif case == 'capitalize':
                val = val.capitalize()
            else:
                val = val.lower()
        out = out.replace(f"{{{name}}}", val, 1)
    return out


def generate_passwords(patterns, words, numbers, specials):
    results = set()
    for pat in patterns:
        tokens = parse_placeholders(pat)
        pools = [{'word': words, 'number': numbers, 'special': specials}[kind]
                 for _, kind, _ in tokens]
        for combo in itertools.product(*pools):
            # skip duplicate word tokens
            word_vals = [v for (n, k, _), v in zip(
                tokens, combo) if k == 'word']
            if len(word_vals) != len(set(word_vals)):
                continue
            results.add(fill_pattern(pat, tokens, combo))
    return results


def has_multi_numeric(pw):
    return len(re.findall(r"\d+", pw)) > 1


def filter_passwords(candidates, min_len, max_len, excluded_groups):
    out = []
    for pw in candidates:
        if not (min_len <= len(pw) <= max_len):
            continue
        if has_multi_numeric(pw):
            continue
        low = pw.lower()
        # Check if password contains any pair combination from excluded groups
        should_exclude = False
        for grp in excluded_groups:
            # For each group, check all possible pairs
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    if grp[i].lower() in low and grp[j].lower() in low:
                        should_exclude = True
                        break
                if should_exclude:
                    break
            if should_exclude:
                break
        if should_exclude:
            continue
        out.append(pw)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default='config.json')
    p.add_argument('--output', help='override output file')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    cfg = load_config(args.config)

    # common pools
    common_words = cfg.get('common_words', [])
    common_numbers = cfg.get('common_numbers', [])
    common_specials = cfg.get('common_special_chars', [])

    # gather every value under "custom"
    custom_values = list(flatten_values(cfg.get('custom', {})))
    generalize_strings = cfg.get('generalize_strings', True)
    personal_items = extract_personal_data(custom_values, generalize_strings)

    # split into words and numbers
    personal_words = [x for x in personal_items if not x.isdigit()]
    personal_numbers = [x for x in personal_items if x.isdigit()]

    words = common_words + personal_words
    numbers = common_numbers + personal_numbers
    specials = [s for s in common_specials if not any(c.isdigit() for c in s)]

    # patterns & case variants
    patterns = cfg.get('word_patterns', [])
    if cfg.get('all_cases', False):
        for pat in list(patterns):
            cap = pat.replace('{word}', '{Word}')
            if cap not in patterns:
                patterns.append(cap)

    # exclusions (list of lists)
    excl = cfg.get('excluded_word_combinations', [])
    if excl and all(isinstance(e, str) for e in excl):
        logging.warning("Wrapping flat exclusions into one group")
        excl = [excl]

    # generate & filter
    min_l = cfg.get('min_length', 1)
    max_l = cfg.get('max_length', 100)
    raw = generate_passwords(patterns, words, numbers, specials)
    good = filter_passwords(raw, min_l, max_l, excl)

    # write output
    out_file = args.output or cfg.get('output_file', 'wordlist.txt')
    with open(out_file, 'w', encoding='utf-8') as f:
        for pw in good:
            f.write(pw + '\n')
        # external wordlist
        ext = cfg.get('external_wordlist', '')
        if ext:
            try:
                for ln in open(ext, 'r', encoding='utf-8', errors='ignore'):
                    if ln.strip():
                        f.write(ln)
            except FileNotFoundError:
                logging.warning(f"External wordlist '{ext}' not found.")

    logging.info(f"Generated {len(good)} passwords.")


if __name__ == '__main__':
    main()
