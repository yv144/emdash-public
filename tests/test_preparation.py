from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd
from openpyxl import Workbook

from utils.cleaning_audit import clean_corpus
from importlib import import_module

add_features = import_module("01_prepare").add_features
from utils.corpus import load_raw_exports, has_abstract


class PreparationTests(unittest.TestCase):
    def test_batches_keep_correction_and_first_copy(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'correction-a').mkdir()
            (root / 'batch').mkdir()
            pd.DataFrame({'EID': ['x','x','y'], 'Abstract': ['correct','duplicate','other']}).to_csv(
                root / 'correction-a' / 'first.csv', index=False)
            pd.DataFrame({'EID': ['x','z',None], 'Abstract': ['stale','third','no id']}).to_csv(
                root / 'batch' / 'other.csv', index=False)
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(['EID','Abstract','Year'])
            sheet.append(['z','stale excel',2024])
            sheet.append(['e','excel',2025])
            workbook.save(root / 'batch' / 'export.xlsx')
            records = load_raw_exports(root, chunksize=1).set_index('eid')
            self.assertEqual(records.abstract.to_dict(), {'x':'correct','y':'other','z':'third','e':'excel'})
            self.assertEqual(records.loc['e','year'], 2025)

    def test_missing_abstract_filter(self):
        records = pd.DataFrame({'abstract': [None,'','  ','[No abstract available]','A—B.']})
        self.assertEqual(has_abstract(records).tolist(), [False,False,False,False,True])

    def test_clean_before_count_and_drop_empty(self):
        records = pd.DataFrame({
            'eid':['x','y','z'], 'year':[2020,2024,2024], 'publisher':['A','A','B'],
            'abstract':['Purpose — Text. Findings — More. © 2020 The Authors.',
                        'Purpose — Text—body; α × 3–5 °C. © 2024 The Authors.',
                        '© 2024 The Authors.']})
        with TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('utils.cleaning_audit.ROOT', root), patch(
                    'utils.cleaning_audit.RESULTS', root / 'results'):
                cleaned = clean_corpus(records, add_features)
            features = add_features(cleaned)
            self.assertEqual(features.eid.tolist(), ['x','y'])
            self.assertEqual(features.count_em.tolist(), [0,1])
            self.assertEqual(features.has_em.tolist(), [False,True])
            self.assertEqual(features.count_en_numeric.tolist(), [0,1])
            self.assertEqual(features.characters.tolist(), [len(t) for t in features.abstract])
            changes = pd.read_csv(root / 'results/preparation/cleaning_marker_changes.csv')
            em = changes[(changes.year.eq('all')) & changes.measure.eq('count_em')].iloc[0]
            self.assertEqual((em.raw,em.cleaned,em.delta), (4,1,-3))
            self.assertEqual(em.n_cleaned, 2)
            self.assertTrue((root / '.cache/cleaning_examples.jsonl').exists())
