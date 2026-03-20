#!/usr/bin/env python3
"""Validate sentences-data.js integrity.
Usage: python3 scripts/validate_sentences_data.py
Exit code 0 = all valid, 1 = errors found.
"""
import json, re, sys, os

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

VALID_VERB_FORMS = {"gerund", "infinitive", "bare"}
REQUIRED_KEYS = {"words", "ru", "verbForm", "keyVerb"}

with open('sentences-data.js', encoding='utf-8') as f:
    content = f.read()

# Extract JSON from JS file
m = re.search(r'window\.sentencesData = (\{[\s\S]+\});', content)
if not m:
    print('ERROR: Cannot parse sentences-data.js')
    sys.exit(1)

data = json.loads(m.group(1))
errors = []

for group_key, sentences in data.items():
    seen_words = []
    for i, s in enumerate(sentences):
        loc = f'{group_key}[{i}]'

        # Required keys
        for key in REQUIRED_KEYS:
            if key not in s:
                errors.append(f'{loc}: missing field "{key}"')

        if 'verbForm' in s and s['verbForm'] not in VALID_VERB_FORMS:
            errors.append(f'{loc}: verbForm="{s["verbForm"]}" not in {VALID_VERB_FORMS}')

        if 'keyVerb' in s and 'words' in s:
            words_str = ' '.join(s['words'])
            if s['keyVerb'] not in words_str:
                errors.append(f'{loc}: keyVerb="{s["keyVerb"]}" not found in words={s["words"]}')

        # Duplicate detection
        words_tuple = tuple(s.get('words', []))
        if words_tuple in seen_words:
            errors.append(f'{loc}: duplicate sentence {s.get("words")}')
        seen_words.append(words_tuple)

if errors:
    print(f'VALIDATION FAILED: {len(errors)} error(s)')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)

total = sum(len(v) for v in data.values())
print(f'OK: {total} sentences validated across {len(data)} groups')
sys.exit(0)
