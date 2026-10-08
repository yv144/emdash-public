"""Apply pure cleaning and write aggregate diagnostics; raw examples stay private."""
from collections import Counter
import json
import random

import pandas as pd

from config import RESULTS, ROOT
from utils.abstract_cleaning import clean_abstract, clean_abstract_with_audit
from utils.data import write_csv


def clean_corpus(corpus, feature_function):
    before = feature_function(corpus.copy())
    rows, examples, cleaned = [], {}, []
    sampled = Counter()
    rng = random.Random(20261005)
    for index, row in enumerate(corpus.itertuples(), 1):
        result = clean_abstract_with_audit(row.abstract)
        if clean_abstract(result.text) != result.text:
            raise AssertionError(f'Non-idempotent cleaning for {row.eid}')
        cleaned.append(result.text)
        audit = {
            'eid': row.eid, 'year': row.year, 'publisher': row.publisher,
            'changed': result.text != row.abstract,
            'copyright_removed': result.copyright_removed,
            'headings_removed': result.headings_removed,
            'leading_em_dash_removed': result.leading_em_dash_removed,
            'empty_after_cleaning': not result.text.strip(),
            'characters_removed': len(row.abstract) - len(result.text),
            'copyright_retained': '©' in result.text,
        }
        rows.append(audit)
        categories = [name for name in ['copyright_removed', 'headings_removed',
                                      'leading_em_dash_removed',
                                      'empty_after_cleaning', 'copyright_retained'] if audit[name]]
        if '—' in row.abstract and '—' not in result.text:
            categories.append('em_positive_removed')
        if not audit['changed']:
            categories.append('unchanged')
        for category in categories:
            sampled[category] += 1
            bucket = examples.setdefault(category, [])
            example = {'category': category, 'eid': row.eid,
                       'before': row.abstract, 'after': result.text}
            if len(bucket) < 25:
                bucket.append(example)
            else:
                slot = rng.randrange(sampled[category])
                if slot < 25:
                    bucket[slot] = example
        if index % 50000 == 0:
            print(f'Cleaned and checked idempotence: {index:,}/{len(corpus):,}', flush=True)
    audit = pd.DataFrame(rows)
    corpus = corpus.copy()
    corpus['abstract'] = cleaned
    after = feature_function(corpus.copy())
    for column in [c for c in before if c.startswith('count_')]:
        if (after[column] > before[column]).any():
            raise AssertionError(f'Cleaning introduced a measured symbol: {column}')
    measurements = []
    # Global and annual changes use the same incoming EIDs; empty cleaned text
    # contributes zero characters/hits and is excluded from the cleaned denominator.
    for year in ['all', *sorted(corpus.year.unique())]:
        mask = pd.Series(True, index=corpus.index) if year == 'all' else corpus.year.eq(year)
        valid = after.abstract.str.strip().ne('')
        for column in ['characters', *[c for c in before if c.startswith(('count_', 'has_'))]]:
            old = int(before.loc[mask, column].sum())
            new = int(after.loc[mask & valid, column].sum())
            measurements.append({'year': year, 'measure': column, 'raw': old,
                                 'cleaned': new, 'delta': new - old,
                                 'n_raw': int(mask.sum()), 'n_cleaned': int((mask & valid).sum())})
    output = RESULTS / 'preparation'
    sums = [c for c in audit if c not in ['eid', 'year', 'publisher']]
    summaries = []
    for group in ['year', 'publisher']:
        summary = audit.groupby(group, dropna=False)[sums].sum().reset_index()
        summary.insert(0, 'group', group)
        summary = summary.rename(columns={group: 'value'})
        summary['n_abstracts'] = audit.groupby(group, dropna=False).size().values
        summaries.append(summary)
    total = {'group': 'all', 'value': 'all', 'n_abstracts': len(audit),
             **{c: int(audit[c].sum()) for c in sums}}
    write_csv(pd.concat([pd.DataFrame([total]), *summaries], ignore_index=True),
              output / 'cleaning_summary.csv')
    write_csv(pd.DataFrame(measurements), output / 'cleaning_marker_changes.csv')
    private = ROOT / '.cache'
    private.mkdir(exist_ok=True)
    write_csv(audit, private / 'cleaning_audit.csv')
    (private / 'cleaning_examples.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n'
                for bucket in examples.values() for row in bucket))
    print('Cleaning:', json.dumps(total), flush=True)
    return corpus[corpus.abstract.str.strip().ne('')].reset_index(drop=True)
