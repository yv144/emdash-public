import math
import unittest

from utils.abstract_cleaning import clean_abstract, clean_abstract_with_audit


class CleaningTests(unittest.TestCase):
    def test_missing_and_unexpected_inputs(self):
        for value in [None, float('nan'), '', ' \t\n', '[No abstract available]']:
            self.assertEqual(clean_abstract(value), '')
        for value in [123, False, [], {}, b'abstract', math.inf]:
            with self.assertRaises(TypeError):
                clean_abstract(value)

    def test_unicode_and_interior_whitespace_are_preserved(self):
        body = 'We measured α—β; 3–5 °C × 2, “é”, e\u0301 and µ/μ.\n  It’s useful &mdash;.'
        self.assertEqual(clean_abstract(body), body)
        self.assertEqual(clean_abstract('Purpose — ' + body + ' Findings — It works.'),
                         body + ' It works.')

    def test_observed_copyright_formats(self):
        notices = [
            '© 2025 The Authors',
            'Copyright. (© 2025 The Authors',
            'Copyright © 2024 Elsevier B.V. All rights reserved.',
            '© 2026 Elsevier Ltd. All rights are reserved, including those for text and data mining, AI training, and similar technologies.',
            '© The Author(s) 2025.',
            '© Springer Nature America, Inc. 2024.',
            '© 2025 by the authors.',
            '© 2021 by the authors. Licensee MDPI, Basel, Switzerland.',
            '© 2024 The Author(s). Advanced Science published by Wiley-VCH GmbH.',
            '© 2024 Copyright held by the owner/author(s). Publication rights licensed to ACM.',
            '© 2019 WILEY-VCH Verlag GmbH & Co. KGaA, Weinheim',
            'Copyright 2020 by the American Thoracic Society.',
            'Copyright of the Academy of Management, all rights reserved.',
            '© ',
        ]
        for notice in notices:
            with self.subTest(notice=notice):
                self.assertEqual(clean_abstract('An effect—α; × °—was observed. ' + notice),
                                 'An effect—α; × °—was observed.')

    def test_prose_and_symbols_are_not_copyright_notices(self):
        for text in [
            'The © symbol—unlike ®—was studied.',
            'We discuss Copyright 2024 reform and its results.',
            'We tested a model. © 2024 accuracy was higher—α remained.',
            'We tested a model. © 2024 The Authors. Additional results follow—α.',
            '© 2024 The Authors. We tested α—β.',
            'Quoted notice: © 2024 The Authors. We tested α—β.',
            'A symbol in prose © without a year remains—α.',
            '–This paper reports an effect. Results: α. Implications: β.',
        ]:
            cleaned = clean_abstract(text)
            if text.startswith('–This'):
                self.assertEqual(cleaned, '–This paper reports an effect. α. β.')
            else:
                self.assertEqual(cleaned, text)

    def test_mixed_and_nested_labels_are_idempotent(self):
        texts = [
            'Purpose — We test α—β. Findings — It works; © 2024 is a symbol.',
            'Background: Results: We test α—β. © 2024 Elsevier Ltd.',
            'Abstract: Purpose: X. Findings: Y. © 2024 The Authors.',
            'Purpose: © 2024 The Authors.',
        ]
        for text in texts:
            result = clean_abstract(text)
            self.assertEqual(clean_abstract(result), result)

    def test_medical_headings_keep_funding_and_registration(self):
        text = ('Importance: We tested α—β. Design, Setting, and Participants: Adults aged 3–5. '
                'Main Outcomes and Measures: Concentration × time. Conclusions and Relevance: Effective. '
                'Funding: Grant A—B. Trial Registration: NCT12345678.')
        self.assertEqual(clean_abstract(text),
                         'We tested α—β. Adults aged 3–5. Concentration × time. Effective. '
                         'Grant A—B. NCT12345678.')

    def test_metadata_does_not_consume_arbitrary_sentences(self):
        self.assertEqual(clean_abstract('Purpose: Test. Category: Patients showed better results. Findings: An effect.'),
                         'Test. Patients showed better results. An effect.')

    def test_oup_permissions_dash_is_removed(self):
        footer = ('© The Author(s) 2026. Published by Oxford University Press on behalf of the Endocrine Society. '
                  'All rights reserved. For commercial re-use, please contact reprints@oup.com for reprints and translation rights for reprints. '
                  'All other permissions can be obtained through our RightsLink service via the Permissions link on the article page on our site'
                  '—for further information please contact journals.permissions@oup.com. See the journal About page for additional terms.')
        self.assertEqual(clean_abstract('A result. ' + footer), 'A result.')
        for end in ['', ' jour', ' journ']:
            truncated = footer.split(' contact journals.permissions')[0] + ' contact' + end
            self.assertEqual(clean_abstract('A result. ' + truncated), 'A result.')
        self.assertEqual(clean_abstract('A result. ' + footer.replace('Society. All', 'Society.All')), 'A result.')
        self.assertEqual(clean_abstract('MATLAB©—R2023b was used; α—β stayed. ' + footer),
                         'MATLAB©—R2023b was used; α—β stayed.')

    def test_glued_medical_em_dashes(self):
        self.assertEqual(clean_abstract('Objectives—Metallic elements matter. Subjects and Methods—Plasma α—β. Conclusions—Various effects.'),
                         'Metallic elements matter. Plasma α—β. Various effects.')

    def test_flags(self):
        result = clean_abstract_with_audit('Purpose — X—Y. © 2024 The Authors.')
        self.assertEqual(result.text, 'X—Y.')
        self.assertTrue(result.copyright_removed)
        self.assertTrue(result.headings_removed)

    def test_leading_em_dash_prefixes(self):
        body = 'Evaluating neurological impairments post-stroke is essential.'
        for prefix in ['—', '— ', ' \t—\n', '—— ', '— \n—\t']:
            with self.subTest(prefix=prefix):
                result = clean_abstract_with_audit(prefix + body)
                self.assertEqual(result.text, body)
                self.assertTrue(result.leading_em_dash_removed)
                self.assertFalse(result.headings_removed)
                self.assertEqual(clean_abstract(result.text), result.text)
        self.assertEqual(clean_abstract(' — \n — '), '')

    def test_leading_rule_preserves_interior_text_and_other_dashes(self):
        body = 'An effect—α; 3–5 °C × 2.\n  More—data &mdash;.'
        self.assertEqual(clean_abstract('— ' + body), body)
        for text in [body, '  ' + body, '– ' + body, '- ' + body,
                     '― ' + body, '&mdash; ' + body, '“—Quoted text.”']:
            self.assertEqual(clean_abstract(text), text)
            self.assertFalse(clean_abstract_with_audit(text).leading_em_dash_removed)

    def test_leading_rule_composes_with_headings_and_copyright(self):
        result = clean_abstract_with_audit(
            '— Text—body. Findings: Effective. Conclusions: Useful. © 2024 The Authors.')
        self.assertEqual(result.text, 'Text—body. Effective. Useful.')
        self.assertTrue(result.copyright_removed)
        self.assertTrue(result.headings_removed)
        self.assertTrue(result.leading_em_dash_removed)
        self.assertEqual(clean_abstract(result.text), result.text)
        # A dash already consumed as a heading separator belongs to that rule.
        result = clean_abstract_with_audit('Purpose: — Text—body.')
        self.assertEqual(result.text, 'Text—body.')
        self.assertTrue(result.headings_removed)
        self.assertFalse(result.leading_em_dash_removed)

    def test_heading_words_and_compounds_in_prose(self):
        for text in [
            'The Results: data varied—substantively.',
            'We have a purpose – a profitable solution – to a problem.',
            'Purpose-driven research informs Design-Build projects.',
            'A method. Findings: one label inside an otherwise unstructured abstract.',
        ]:
            self.assertEqual(clean_abstract(text), text)
