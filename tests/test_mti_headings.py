"""Structured-abstract headings: which labels are removed, and which uses of the same words are kept."""
from pathlib import Path
import sys
import unittest

from utils.abstract_cleaning import strip_headings


class HeadingTests(unittest.TestCase):
    def test_emerald_headings_with_each_separator(self):
        for sep in [': ', ' – ', ' - ', ' — ', '-', ': – ']:
            text = (f'Purpose{sep}The aim is X. Design/methodology/approach{sep}We survey firms. '
                    f'Findings{sep}Y holds. Originality/value{sep}New.')
            self.assertEqual(strip_headings(text), 'The aim is X. We survey firms. Y holds. New.', sep)

    def test_other_formats(self):
        cases = {
            'Background: B. Objectives: O. Methods/Approach: M. Results: R. Conclusions: C.': 'B. O. M. R. C.',
            'INTRODUCTION: I. OBJECTIVES: O. METHODS: M.': 'I. O. M.',
            'Introduction. I. Problem Statement. P. Materials and Methods. M. Results. R.': 'I. P. M. R.',
            ': OVERVIEW: Text.': 'Text.',
            'Abstract Purpose – X. Findings – Y.': 'X. Y.',
            'Manuscript Type: Empirical. Research Question/Issue: Q. Research Findings/Insights: F.': 'Q. F.',
            'Manuscript Type: EmpiricalResearch Question/Issue: Q. Practitioner/Policy Implications: P.': 'Q. P.',
            'Purpose: X. Findings: Y. Category: Research paper.': 'X. Y.',
            '–This paper aims at X. Results: Y. Implication: Z.': '–This paper aims at X. Y. Z.',
            'Purpose: X. Material and Methods. M. Research results. R. Findings –. The F.': 'X. M. R. The F.',
            'Purpose: X. Design/methodological/approach: M. Methods/approaches: A. Method-This study. Approach-A model.':
                'X. M. A. This study. A model.',
        }
        for text, expected in cases.items():
            self.assertEqual(strip_headings(text), expected, text)

    def test_section_boundaries(self):
        # A ';' joining sections, a heading glued to the previous sentence, a sentence without a full stop.
        self.assertEqual(strip_headings('Purpose: X.; Findings – Y.'), 'X. Y.')
        self.assertEqual(strip_headings('Purpose: X.Findings: Y.'), 'X. Y.')
        self.assertEqual(strip_headings('Purpose - X of the company Design/methodology/approach - Y.'), 'X of the company Y.')

    def test_headings_without_separators(self):
        # Emerald abstracts without separators, some with hyphens for slashes; at least two such labels are needed.
        text = ('Purpose To investigate X. Design-methodology-approach From interviews. Findings Brands fail. '
                'Research limitations-implications The study is small. Originality-value While rich.')
        self.assertEqual(strip_headings(text), 'To investigate X. From interviews. Brands fail. The study is small. '
                                               'While rich.')
        for text in ['Purpose The purpose of branding is growth. Value Chain analysis follows.',
                     'Findings Suggest that design matters. Practical implications are discussed.']:
            self.assertEqual(strip_headings(text), text)

    def test_single_summary_label_marks_a_structured_abstract(self):
        self.assertEqual(strip_headings('We find X. Executive summary: Directors matter.'), 'We find X. Directors matter.')
        self.assertEqual(strip_headings('We find X. Managerial Summary: Y.'), 'We find X. Y.')

    def test_words_in_sentences_are_kept(self):
        for text in ['Firms declare a purpose – a profitable solution – to the problems. Purpose-driven firms grow.',
                     'The results: firms grow. Findings-based policy is rare.',
                     'We study X. Findings: one heading only.',  # a single heading within the text
                     'Plain text about corporate purpose and its value.']:
            self.assertEqual(strip_headings(text), text)
        self.assertEqual(strip_headings('Purpose: X (Design-Build). Findings – Results- and job-oriented cultures. '
                                        'Value-Added firms (STS) Theory. Design-Build works. Approach-Avoidance too.'),
                         'X (Design-Build). Results- and job-oriented cultures. Value-Added firms (STS) Theory. '
                         'Design-Build works. Approach-Avoidance too.')

    def test_idempotent(self):
        text = 'Manuscript Type: Empirical Research Question/Issue: Q. Research Findings/Insights: F.'
        self.assertEqual(strip_headings(strip_headings(text)), strip_headings(text))
        self.assertIsNone(strip_headings(None))


if __name__ == '__main__':
    unittest.main()
