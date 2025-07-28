#!/usr/bin/env python
import argparse
import itertools
import json
import logging
import re
import unicodedata
import os


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_list_from_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def generalize_string(s):
    normalized = unicodedata.normalize('NFD', s)
    stripped = ''.join(
        c for c in normalized if unicodedata.category(c) != 'Mn')
    return unicodedata.normalize('NFC', stripped)


def parse_placeholders(pattern):
    tokens = []
    for m in re.finditer(r"\{(.*?)\}", pattern):
        name = m.group(1)
        base = name.rstrip('*')
        wildcard = name.endswith('*')
        if re.match(r'(?i)word\d*$', base):
            case = 'any' if wildcard else 'upper' if base.isupper(
            ) else 'capitalize' if base[0].isupper() else 'lower'
            tokens.append((name, 'word', case))
        elif base == 'number':
            tokens.append((name, 'number', None))
        elif base == 'special':
            tokens.append((name, 'special', None))
    return tokens


def fill_pattern(pattern, tokens, values):
    out = pattern
    for (name, kind, case), val in zip(tokens, values):
        if kind == 'word' and case != 'any':
            val = val.upper() if case == 'upper' else val.capitalize(
            ) if case == 'capitalize' else val.lower()
        out = out.replace(f"{{{name}}}", val, 1)
    return out


def generate_passwords(patterns, words, numbers, specials):
    results = set()
    for pat in patterns:
        tokens = parse_placeholders(pat)
        pools = []
        for name, kind, case in tokens:
            base_pool = {'word': words, 'number': numbers,
                         'special': specials}[kind]
            if kind == 'word' and case == 'any':
                variants = set()
                for w in base_pool:
                    variants.add(w.lower())
                    variants.add(w.capitalize())
                    variants.add(w.upper())
                pools.append(list(variants))
            else:
                pools.append(base_pool)

        for combo in itertools.product(*pools):
            word_vals = [v for (n, k, _), v in zip(
                tokens, combo) if k == 'word']
            if len(word_vals) != len(set(word_vals)):
                continue
            results.add(fill_pattern(pat, tokens, combo))
    return results


def filter_passwords(candidates, min_len, max_len, word_groups, number_groups, special_groups):
    filtered = []
    for pw in candidates:
        if not (min_len <= len(pw) <= max_len):
            continue
        low = pw.lower()

        # Check word conflicts
        word_conflict = any(
            sum(1 for w in group if w.lower() in low) > 1
            for group in word_groups if len(group) > 1
        )
        if word_conflict:
            continue

        # Check number conflicts
        number_conflict = any(
            sum(1 for n in group if n in pw) > 1
            for group in number_groups if len(group) > 1
        )
        if number_conflict:
            continue

        # Check special character conflicts
        special_conflict = any(
            sum(1 for s in group if s in pw) > 1
            for group in special_groups if len(group) > 1
        )
        if special_conflict:
            continue

        filtered.append(pw)
    return filtered


def parse_word_groups(value):
    groups = []
    words = []
    for g in value.split(';'):
        group = [w.strip() for w in g.split(',') if w.strip()]
        if group:
            groups.append(group)
            words.extend(group)
    return words, groups


def parse_semicolon_list(value):
    return [item.strip() for item in value.split(';') if item.strip()]


def parse_number_groups(value):
    groups = []
    numbers = []
    for g in value.split(';'):
        if ',' in g:
            group = [w.strip() for w in g.split(',') if w.strip()]
            if group:
                groups.append(group)
                numbers.extend(group)
        else:
            item = g.strip()
            if item:
                numbers.append(item)
    return numbers, groups


def parse_special_groups(value):
    groups = []
    specials = []
    for g in value.split(';'):
        if ',' in g:
            group = [w.strip() for w in g.split(',') if w.strip()]
            if group:
                groups.append(group)
                specials.extend(group)
        else:
            item = g.strip()
            if item:
                specials.append(item)
    return specials, groups


def main():

    parser = argparse.ArgumentParser(
        description='Weaver - Generate wordlist for password testing')
    parser.add_argument(
        '--patterns', help='Pattern string using DSL like "WnS;WwS" (see --pattern-mode)')
    parser.add_argument(
        '--words', help='Grouped by commas, separated by semicolon or @file')
    parser.add_argument('--numbers', help='Semicolon-separated or @file')
    parser.add_argument(
        '--specials', help='String, semicolon-separated or @file')
    parser.add_argument('--output', default='wordlist.txt',
                        help='Output file path')
    parser.add_argument('--min-length', type=int, default=1,
                        help='Minimum password length')
    parser.add_argument('--max-length', type=int,
                        default=100, help='Maximum password length')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--normalize', action='store_true', default=False,
                        help='Enable Unicode normalization (default: off)')
    parser.add_argument('--pattern-mode', choices=['as-is', 'cap', 'any'], default='as-is',
                        help='How to interpret pattern cases: as-is (default), cap (lower + capitalized), any (lower + uppercase + capitalized)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    if not args.patterns:
        logging.error("No patterns provided")
        return
    patterns = []
    for p in args.patterns.split(';'):
        p = p.strip()
        out = []
        for i, ch in enumerate(p):
            if ch.lower() == 'w':
                if args.pattern_mode == 'any':
                    out.append(f'{{word{i}*}}')
                elif args.pattern_mode == 'cap':
                    out.append(f'{{word{i}}}')
                else:
                    out.append(f'{{word{i}}}')
            elif ch.lower() == 'n':
                out.append('{number}')
            elif ch.lower() == 's':
                out.append('{special}')
            else:
                logging.warning(f'Unsupported pattern character: {ch}')
        patterns.append(''.join(out))

    if args.words or args.numbers or args.specials:
        if args.words:
            if args.words.startswith('@'):
                words = load_list_from_file(args.words[1:])
                word_groups = []
            else:
                words, word_groups = parse_word_groups(args.words)
        else:
            words, word_groups = [], []

        if args.numbers:
            if args.numbers.startswith('@'):
                numbers = load_list_from_file(args.numbers[1:])
                number_groups = []
            else:
                numbers, number_groups = parse_number_groups(args.numbers)
        else:
            numbers, number_groups = [], []

        if args.specials:
            if args.specials.startswith('@'):
                specials = load_list_from_file(args.specials[1:])
                special_groups = []
            elif ';' in args.specials:
                specials, special_groups = parse_special_groups(args.specials)
            else:
                specials = list(args.specials)
                special_groups = []
        else:
            specials, special_groups = [], []

    else:
        words = []
        numbers = []
        specials = []
        word_groups = []
        number_groups = []
        special_groups = []

    if args.normalize:
        words = list({generalize_string(w) for w in words})

    raw = generate_passwords(patterns, words, numbers, specials)
    good = filter_passwords(raw, args.min_length, args.max_length,
                            word_groups, number_groups, special_groups)

    with open(args.output, 'w', encoding='utf-8') as f:
        for pw in sorted(good):
            f.write(pw + '\n')

    logging.info(f"Generated {len(good)} passwords to {args.output}")
    logging.info(
        f"Used {len(words)} words, {len(numbers)} numbers, {len(specials)} special chars")
    all_groups = len(word_groups) + len(number_groups) + len(special_groups)
    logging.info(f"Applied {all_groups} conflict rules")


if __name__ == '__main__':
    main()
