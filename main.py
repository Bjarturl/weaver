#!/usr/bin/env python3
import argparse
import itertools
import json
import logging
import re
import unicodedata

ICELANDIC_REPLACEMENTS = {
    'ð': 'd', 'Ð': 'D',
    'þ': 'th', 'Þ': 'Th',
    'æ': 'ae', 'Æ': 'Ae',
    'ø': 'o', 'Ø': 'O'
}


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generalize_string(s):
    result = s
    for old, new in ICELANDIC_REPLACEMENTS.items():
        result = result.replace(old, new)
    normalized = unicodedata.normalize('NFD', result)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


def flatten_values(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from flatten_values(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten_values(item)
    elif isinstance(obj, (str, int, float)):
        yield obj


def extract_personal_data(values, generalize_strings=True):
    items = []
    for raw in values:
        s = str(raw).lower()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            y, m, d = s.split('-')
            items.extend([y, y[-2:], m, d, m + d, d + m])
        else:
            for w in s.split():
                if len(w) > 1 and not w.isdigit():
                    if generalize_strings:
                        gen = generalize_string(w)
                        if gen != w and generalize_strings == "both":
                            items.append(w)
                            items.append(gen)
                        else:
                            items.append(gen if gen != w else w)
                    else:
                        items.append(w)
        items.extend(re.findall(r"\d+", s))
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
    out = pattern
    for (name, kind, case), val in zip(tokens, values):
        if kind == 'word':
            val = val.upper() if case == 'upper' else val.capitalize(
            ) if case == 'capitalize' else val.lower()
        out = out.replace(f"{{{name}}}", val, 1)
    return out


def generate_passwords(patterns, words, numbers, specials):
    results = set()
    for pat in patterns:
        tokens = parse_placeholders(pat)
        pools = [{'word': words, 'number': numbers, 'special': specials}[kind]
                 for _, kind, _ in tokens]
        for combo in itertools.product(*pools):
            word_vals = [v for (n, k, _), v in zip(
                tokens, combo) if k == 'word']
            if len(word_vals) != len(set(word_vals)):
                continue
            results.add(fill_pattern(pat, tokens, combo))
    return results


def has_multi_numeric(pw):
    return len(re.findall(r"\d+", pw)) > 1


def filter_passwords(candidates, min_len, max_len, excluded_groups):
    filtered = []
    for pw in candidates:
        if not (min_len <= len(pw) <= max_len):
            continue
        if has_multi_numeric(pw):
            continue
        low = pw.lower()
        conflict = any(
            low.count(a.lower()) and low.count(b.lower())
            for grp in excluded_groups
            for a in grp
            for b in grp
            if a != b
        )
        if conflict:
            continue
        filtered.append(pw)
    return filtered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--output')
    parser.add_argument('--external-wordlist')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    cfg = load_config(args.config)

    all_values = list(flatten_values(cfg.get('words', {})))
    gen_strings = cfg.get('generalize_strings', True)
    items = extract_personal_data(all_values, gen_strings)

    words = [x for x in items if not x.isdigit()]
    numbers = [x for x in items if x.isdigit()]
    specials = [s for s in all_values if isinstance(
        s, str) and not s.isdigit() and not s.isalpha()]

    patterns = cfg.get('word_patterns', [])
    if cfg.get('all_cases', False):
        # Generate capitalized variations for all word placeholders
        case_variants = []
        for pat in patterns:
            # Find all word placeholders in the pattern
            word_placeholders = re.findall(
                r'\{(word\d*)\}', pat, re.IGNORECASE)
            if word_placeholders:
                # Generate all case combinations for this pattern (lowercase + capitalized)
                case_combinations = []
                for placeholder in word_placeholders:
                    # Create variations: lowercase, Capitalized (first letter only)
                    case_combinations.append([
                        placeholder.lower(),
                        placeholder.lower().capitalize()
                    ])

                # Generate all possible combinations
                for combo in itertools.product(*case_combinations):
                    new_pattern = pat
                    for old_placeholder, new_placeholder in zip(word_placeholders, combo):
                        # Replace the first occurrence of each placeholder
                        old_tag = f"{{{old_placeholder}}}"
                        new_tag = f"{{{new_placeholder}}}"
                        new_pattern = new_pattern.replace(old_tag, new_tag, 1)

                    if new_pattern not in patterns:
                        case_variants.append(new_pattern)

        patterns.extend(case_variants)

    excl = cfg.get('excluded_word_combinations', [])
    if excl and all(isinstance(e, str) for e in excl):
        excl = [excl]

    raw = generate_passwords(patterns, words, numbers, specials)
    good = filter_passwords(raw, cfg.get('min_length', 1),
                            cfg.get('max_length', 100), excl)

    out_path = args.output or cfg.get('output_file', 'wordlist.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        for pw in good:
            f.write(pw + '\n')
        if args.external_wordlist:
            try:
                with open(args.external_wordlist, 'r', encoding='utf-8', errors='ignore') as ef:
                    for ln in ef:
                        if ln.strip():
                            f.write(ln)
            except FileNotFoundError:
                logging.warning(
                    f"External wordlist '{args.external_wordlist}' not found.")

    logging.info(f"Generated {len(good)} passwords.")


if __name__ == '__main__':
    main()
