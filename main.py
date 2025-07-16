#!/usr/bin/env python3
import argparse
import itertools
import json
import logging
import re


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_personal_data(info):
    items = []
    for v in info.values():
        if not v:
            continue
        if isinstance(v, list):
            items.extend(str(x).lower() for x in v if x)
        else:
            s = str(v).lower()
            if re.match(r"\d{4}-\d{2}-\d{2}", s):
                y, m, d = s.split('-')
                items += [y, y[-2:], m, d, m + d, d + m]
            elif ' ' in s:
                items += [w for w in s.split() if len(w) > 1]
            else:
                items.append(s)
            items += re.findall(r"\d+", s)
    return items


def parse_placeholders(pattern):
    tokens = []
    for m in re.finditer(r"\{(.*?)\}", pattern):
        name = m.group(1)
        if re.match(r'(?i)word\d*$', name):
            case = 'upper' if name.isupper(
            ) else 'capitalize' if name[0].isupper() else 'lower'
            tokens.append((name, 'word', case))
        elif name == 'number':
            tokens.append((name, 'number', None))
        elif name == 'special':
            tokens.append((name, 'special', None))
    return tokens


def fill_pattern(pattern, tokens, values):
    result = pattern
    for (name, kind, case), val in zip(tokens, values):
        if kind == 'word':
            if case == 'upper':
                val = val.upper()
            elif case == 'capitalize':
                val = val.capitalize()
            else:
                val = val.lower()
        # replace the exact placeholder
        result = result.replace(f"{{{name}}}", val, 1)
    return result


def generate_passwords(patterns, words, numbers, specials):
    out = set()
    for pat in patterns:
        tokens = parse_placeholders(pat)
        pools = []
        for _, kind, _ in tokens:
            if kind == 'word':
                pools.append(words)
            elif kind == 'number':
                pools.append(numbers)
            elif kind == 'special':
                pools.append(specials)
        for combo in itertools.product(*pools):
            pwd = fill_pattern(pat, tokens, combo)
            out.add(pwd)
    return out


def has_multi_numeric(p):
    return len(re.findall(r"\d+", p)) > 1


def filter_passwords(pws, min_len, max_len, excluded):
    result = []
    for p in pws:
        if not (min_len <= len(p) <= max_len):
            continue
        if has_multi_numeric(p):
            continue
        low = p.lower()
        count = sum(1 for w in excluded if w.lower() in low)
        if count >= 2:
            continue
        result.append(p)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--output', help='override output file')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    cfg = load_config(args.config)

    common_words = cfg.get('common_words', [])
    common_numbers = cfg.get('common_numbers', [])
    common_specials = cfg.get('common_special_chars', [])

    custom = cfg.get('custom', {})
    custom_words = custom.get('words', [])
    custom_numbers = custom.get('numbers', [])
    personal_info = custom.get('personal_info', {})

    personal = extract_personal_data(personal_info)
    personal_words = [x for x in personal if not x.isdigit()]
    personal_numbers = [x for x in personal if x.isdigit()]

    words = common_words + custom_words + personal_words
    numbers = common_numbers + custom_numbers + personal_numbers
    specials = [s for s in common_specials if not any(c.isdigit() for c in s)]

    patterns = cfg.get('word_patterns', [])
    if cfg.get('all_cases', False):
        duplicates = []
        for pat in patterns:
            duplicates.append(pat.replace('{word}', '{Word}'))
        for dup in duplicates:
            if dup not in patterns:
                patterns.append(dup)

    excluded = cfg.get('excluded_word_combinations', [])
    min_len = cfg.get('min_length', 1)
    max_len = cfg.get('max_length', 100)

    pw_set = generate_passwords(patterns, words, numbers, specials)
    filtered = filter_passwords(pw_set, min_len, max_len, excluded)

    out_path = args.output or cfg.get('output_file', 'wordlist.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        for pwd in filtered:
            f.write(pwd + '\n')
        ext = cfg.get('external_wordlist', '')
        if ext:
            try:
                with open(ext, 'r', encoding='utf-8', errors='ignore') as ef:
                    for ln in ef:
                        if ln.strip():
                            f.write(ln)
            except FileNotFoundError:
                logging.warning(f"External wordlist '{ext}' not found.")

    logging.info(f"Generated {len(filtered)} passwords.")


if __name__ == '__main__':
    main()
