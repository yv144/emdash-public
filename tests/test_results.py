import unittest

import numpy as np
import pandas as pd

from config import DATA, RESULTS


class ManuscriptResults(unittest.TestCase):
    def test_count_tables(self):
        yearly = pd.read_csv(DATA / "yearly_counts.csv.gz")
        quarterly = pd.read_csv(DATA / "quarterly_counts.csv.gz")
        self.assertEqual(yearly.n_abstracts.sum(), 615299)
        self.assertEqual(yearly.hits_em.sum(), 23637)
        self.assertEqual(yearly.journal.nunique(), 487)
        self.assertEqual(quarterly.n_abstracts.sum(), 599052)
        self.assertEqual(quarterly.loc[quarterly.year_quarter.le("2026Q1"), "n_abstracts"].sum(), 569927)
        for counts in [yearly, quarterly]:
            hits = counts.filter(regex="^hits_")
            self.assertTrue(hits.ge(0).all().all())
            self.assertTrue(hits.le(counts.n_abstracts, axis=0).all().all())

    def test_periods_and_subgroups(self):
        annual = pd.read_csv(RESULTS / "prevalence/annual.csv")
        np.testing.assert_allclose(annual.pct_em, 100 * annual.hits_em / annual.n_abstracts)
        period = pd.read_csv(RESULTS / "prevalence/period_comparison.csv").iloc[0]
        self.assertEqual((period.n_baseline, period.n_post), (271959, 343340))
        self.assertAlmostEqual(period.pct_baseline, 3.06, places=2)
        self.assertAlmostEqual(period.pct_post, 4.46, places=2)
        areas = pd.read_csv(RESULTS / "subgroups/areas.csv")
        publishers = pd.read_csv(RESULTS / "subgroups/publishers.csv")
        self.assertEqual((len(areas), len(publishers)), (17, 11))
        self.assertEqual(areas.change_pp.gt(0).sum(), 16)
        self.assertTrue(publishers.change_pp.gt(0).all())

    def test_models(self):
        result = pd.read_csv(RESULTS / "time_series/breakpoint.csv").iloc[0]
        self.assertAlmostEqual(result.psi, 2024.44, places=2)
        self.assertAlmostEqual(result.fitted_end, 7.50, places=2)
        self.assertAlmostEqual(result.cf_end, 2.49, places=2)
        contrasts = pd.read_csv(RESULTS / "markers/slope_comparisons.csv")
        self.assertEqual(len(contrasts), 8)
        self.assertTrue(contrasts.difference_log_odds_per_quarter.gt(0).all())
        self.assertTrue(contrasts.p_holm.lt(0.001).all())

    def test_validation(self):
        result = pd.read_csv(RESULTS / "validation/summary.csv").iloc[0]
        self.assertEqual((result.reviewed, result.agreement), (800, 795))
        self.assertAlmostEqual(result.adjusted_change_pp, 0.86, places=2)
