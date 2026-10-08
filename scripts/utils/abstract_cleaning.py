"""Clean headings, terminal copyright notices, and leading em dashes.

Heading and copyright rules adapted from MTI Lang,
commit dfd31d9d1f11ee708ab815c50750d242ddb7a3d5.
"""
from dataclasses import dataclass
import math
import re

# Labels require an initial capital; separators allow spacing and slash/hyphen variants.
LABELS = '''
abstract; academic abstract; academic summary; managerial summary; research summary; practitioner summary;
executive summary;
overview; summary; highlights; editor's note; introduction; introductions; introduction/main objective; introduction/main objectives;
background; background of the study; background of the problem; background problem; background problems; context; problem; problem statement;
subject matter; relevance; novelty; scientific novelty; significance; scope; problems;
purpose; purposes; research purpose; purpose of the study; purpose of the research; purpose of the paper; aim; aims; aim of the study;
goal; goals; objective; objectives; study objective; objective of the study; research objective; research objectives; main objectives;
tasks; research question; research questions; research question/issue; research question/issues;
research questions/issue; research questions/issues; question/issue; research issue;
design; approach; method; methods; methodology; methods/approach; methodology/approach; design/methodology;
design/methodology/approach; design methodology/approach; design/methodology approach; design methodology approach;
design/methodological/approach; design/methodolog/approach; design/methodology/approachx; methods/approaches;
research design; research method; research methods;
research methodology; materials; materials and methods; material and methods; case description;
findings; finding; results; result; main results; principal results; main findings; key findings; research findings;
research finding; research findings/insights; research findings/insight; research findings/results; research insights;
finding/results; findings/results; finding/result; research results; research result; analysis and results;
results and conclusions; results and contributions;
contributions and results; discussion; discussions; discussion and evaluation;
conclusion; conclusions; major conclusions; conclusion and contribution; contribution; contributions;
main contributions; practical contributions; theoretical contribution; theoretical contributions;
social contributions; contributions to society;
management contributions; managerial contributions; theoretical/methodological contributions;
social/management contributions; social/managerial contributions;
implication; implications; practical implication; practical implications; pratical implication;
pratical implications; practicable implications; practical/implications; practical applications;
social implications; social/implications; practical and social implications; managerial implications; policy implications;
practical/policy implications; practice/policy implications; practitioner implications;
practitioner/policy implications; practitioner/policy implication; practitioner takeaways; research implications;
research/practical implications; theoretical implications; academic implications; theoretical/academic implications;
theoretic/academic implications; implications for theory and practice; limitation; limitations; research limitation;
research limitations; research limitation/implication; research limitation/implications;
research limitations/implication; research limitations/implications; research limitations/implictions;
research/limitations/implications;
research limitations implications; research limitations and implications; research implications and limitations;
limitation/implication; limitation/implications; limitations of the investigation; limitation of the investigation;
limitations of investigation; limitations of the investigations; limitations of the research;
researchlimitations/implications; originality; value; originality/value; original/value; originality value; original value; originality/values;
originality and value; originality/value of paper; originality/value of the paper; value of paper; value of the paper;
originality/relevance; relevance and originality;
dilemma; theory; options; protagonist; case context; basis of the case; type of the case; type of case;
phenomenon studied; link to theory; links to theory; discussions and case questions; discussion and case questions;
manuscript type; manuscript tytpe; category; paper type;
вступ
'''
# Additional clinical and review headings.
LABELS += ''';
importance; interpretation; funding; rationale; scope and approach;
key findings and conclusions; design, setting, and participants;
design, setting and participants; main outcomes and measures;
exposure; exposures; intervention; interventions; setting; participants;
patient summary; trial registration; registration; methods and results;
results and limitations; outcome measurements and statistical analysis;
background and objective; background and objectives; key findings and limitations;
conclusions and clinical implications; conclusions and relevance;
data sources; study selection; data extraction and synthesis;
study question; summary answer; what is known already; study design, size, duration;
participants/materials, setting, methods; main results and the role of chance;
limitations, reasons for caution; wider implications of the findings;
study funding/competing interests; trial registration number;
summary background data; evidence acquisition; evidence synthesis;
context and objective; objective and methods; methods and materials; subjects and methods
'''
# Article-type labels consume their short metadata value.
METADATA = {'manuscript type', 'manuscript tytpe', 'category', 'paper type'}
METADATA_VALUE = re.compile(
    r'(?:Empirical(?: research)?|Research paper|Research article|Review(?: paper| article)?|'
    r'Conceptual(?: paper| article)?|Case study|General review|Literature review|'
    r'Technical paper|Viewpoint)\b', re.I)
# Emerald headings accept attached separators, as in 'Purpose-The ...'.
GLUED = {'purpose', 'design/methodology/approach', 'findings', 'originality/value', 'practical implications',
         'research limitations/implications', 'social implications'}
# Other labels take a touching dash only before a word that starts a sentence ('Method-This study ...').
OPENERS = {'The', 'This', 'These', 'A', 'An', 'We', 'Our', 'In', 'It', 'To', 'Using', 'By', 'For'}
CLINICAL_GLUED = {'objective', 'objectives', 'background', 'methods', 'subjects and methods',
                  'results', 'conclusion', 'conclusions'}
# Bare Emerald headings require two distinct labels.
BARE = GLUED
# Distinctive labels identify structured abstracts on their own.
STANDALONE = {'executive summary', 'managerial summary', 'research summary', 'academic summary', 'practitioner summary',
              'design/methodology/approach', 'originality/value', 'research limitations/implications',
              'practical implications', 'social implications'}
ITEMS = sorted({' '.join(item.split()) for item in LABELS.split(';') if item.strip()}, key=lambda item: (-len(item), item))
DASHES = '–—-'
# Characters after which a capitalized label starts a new section rather than continuing a sentence.
SENTENCE_END = '.!?;:"”’\''


def _item(label):
    words = [r'\s*[/-]\s*'.join(re.escape(part).replace("'", "['’]") for part in word.split('/'))
             for word in label.split(' ')]
    return r'\s+'.join('(?:and|&)' if word == 'and' else word for word in words)


_ITEM = '(?:' + '|'.join(map(_item, ITEMS)) + ')'
_LABEL = rf'(?i:{_ITEM}(?:\s*/\s*{_ITEM})*)'
# Include an 'Abstract' prefix attached to a heading.
_PREFIX = r'(?:(?:Abstract|ABSTRACT)\s+)?'
# A separator ('Findings –. The ...' has a stray period), or none before a capital (see BARE).
HEADING_AT = re.compile(
    rf'''(?P<label>{_PREFIX}{_LABEL})(?P<sep>(?:\s*[:{DASHES}])+\.?|\.|(?=\s+[A-Z]))(?P<space>\s*)''')
HEADING = re.compile(rf'''(?<![\w\-/&'’])(?=[A-ZА-ЯІЇЄ]){HEADING_AT.pattern}''')
# A metadata value: at most six short words, ending at a period, the next heading or the end of the text.
VALUE = re.compile(rf'''[A-Za-z]+?(?:[ /-]+[A-Za-z]+?){{0,5}}?(?:\s*\.(?=\s|$)\s*|(?=\s*{_LABEL}\s*[:{DASHES}])\s*|\s*$)''')


def normalize(label):
    label = re.sub(r'\s*[/-]\s*', '/', label.lower().replace('&', 'and').replace('’', "'"))
    return re.sub(r'^abstract (?=\S)', '', re.sub(r'\s+', ' ', label))


def _accepted(text, match, previous_end):
    """Classify a heading boundary as start, strict, loose, or None."""
    label, sep, space = match.group('label', 'sep', 'space')
    if not label[0].isupper():
        return None
    start, end = match.start(), match.end()
    before = text[:start]
    following = text[end:end + 1]
    if not before.strip(' \t\n\r:;,.' + DASHES):
        kind = 'start'
    elif previous_end == start or before.rstrip()[-1] in SENTENCE_END:
        kind = 'strict'
    elif before[-1].isspace() and not before.split()[-1][0].isupper():
        kind = 'loose'  # e.g. '... for health insurance business Design/Methodology/Approach: ...'
    else:
        return None
    if not sep:
        return kind if kind != 'loose' and normalize(label) in BARE else None
    dash = sep.strip()[-1] in DASHES
    if sep == '.':
        # 'Results. ...' only as its own sentence, not '... (STS) Theory. ...'
        sentence = kind == 'start' or previous_end == start or re.search(r'''[.!?]["”’']?\s*$''', before)
        return kind if sentence and space else None
    if sep in DASHES and not space:
        # 'Purpose-The ...', 'Method-This ...' at a sentence boundary; not a compound such as 'Design-Build'.
        word = re.match(r'[A-Za-z]*', text[end:]).group()
        return kind if kind != 'loose' and following.isupper() and (
            normalize(label) in GLUED or word in OPENERS or
            (sep == '—' and normalize(label) in CLINICAL_GLUED)) else None
    if dash and not (space and sep[0].isspace()) and not (following.isupper() or following.isdigit() or not following):
        return None  # 'Results- and job-oriented', a suspended hyphen
    if not space and not (following.isupper() or following.isdigit() or following in '([“"‘\'' or not following):
        return None
    return kind


def heading_spans(text):
    """Return removal spans for headings in a structured abstract."""
    text = text or ''
    found, previous_end, position = [], None, 0
    while True:
        # Metadata values can run into the next label: 'EmpiricalResearch Question:'.
        glued = previous_end == position and position and text[position - 1].isalpha()
        match = (glued and HEADING_AT.match(text, position)) or HEADING.search(text, position)
        if not match:
            break
        position = match.end()
        kind = _accepted(text, match, previous_end)
        if kind is None:
            continue
        end = match.end()
        if normalize(match.group('label')) in METADATA:
            value = VALUE.match(text, end)
            if value and METADATA_VALUE.fullmatch(value.group().strip().rstrip('.').strip()):
                end = position = value.end()
        found.append((match.start(), end, kind, normalize(match.group('label')), not match.group('sep')))
        previous_end = end
    if len({label for *_, label, bare in found if bare}) < 2:
        found = [heading for heading in found if not heading[-1]]
    sentence = [(label, kind) for _, _, kind, label, _ in found if kind != 'loose']
    labels = {label for label, _ in sentence}
    if not sentence or not (sentence[0][1] == 'start' or len(labels) >= 2 or labels & STANDALONE):
        return []
    spans = []
    for start, end, kind, *_ in found:
        if kind == 'start':
            start = 0  # with any separator left before the first heading ('–This paper ...', ': OVERVIEW: ...')
        else:
            # A ';' that Scopus put between the previous section's final punctuation and the heading.
            joined = re.search(r'''[.!?)"”’]\s*(;\s*)$''', text[:start])
            if joined:
                start = joined.start(1)
        spans.append((start, end))
    return spans


def strip_headings(text):
    """The text without its structured-abstract headings; one space replaces a heading between two words."""
    spans = heading_spans(text)
    if not spans:
        return text
    parts, position = [], 0
    for start, end in spans:
        parts.append(text[position:start])
        if parts[-1] and not parts[-1][-1].isspace() and end < len(text) and not text[end].isspace():
            parts.append(' ')
        position = end
    parts.append(text[position:])
    return ''.join(parts).strip()

# Terminal copyright notices and their accepted legal clauses.
_COPYRIGHT = re.compile(r"(?:Copyright[\s.:(-]*)?©\s*|Copyright\s+(?=\d{4}\b)", re.I)
_YEAR = re.compile(r"\(?\s*(?:19|20)\d{2}\b(?:\s*[-–]\s*(?:19|20)?\d{2})?\)?[.,]?\s*")
_RIGHTS = re.compile(
    r"(?:All rights (?:are )?reserved(?:, including those for text and data mining, "
    r"AI training, and similar technologies)?\.?|Some rights reserved\.?|"
    r"Publication rights licensed to ACM\.?|"
    r"(?:[A-Z][\w &,-]+ )?[Pp]ublished (?:by|on behalf of|with license by) .+|"
    r"Licensee MDPI, Basel, Switzerland\.?|"
    r"This (?:is an open access article|article is (?:an open access|distributed|licensed|published and distributed))\b.+|"
    r"Distributed under\b.+|Open Access\b.+|Creative Commons\b.+|"
    r"For commercial re-use, please contact reprints@oup\.com for reprints and translation rights for reprints\.|"
    r"All other permissions can be obtained through our RightsLink service via the Permissions link on the article page on our site"
    r"—for further information please contact(?: (?:journals\.permissions@oup\.com\.?|journ?))?|"
    r"See the journal About page for additional terms\.|"
    r"For permissions, please (?:e-mail|email):? journals\.permissions@oup\.com\.?)", re.S | re.I)
_PROSE = re.compile(
    r"\b(?:we|our|they|their|was|were|is|are|has|have|had|show|shows|showed|"
    r"found|find|finds|used|uses|using|studied|demonstrates|demonstrated|"
    r"suggests|suggested|investigate|investigated|indicates|indicated|increased|"
    r"decreased|results|methods|conclusions|background)\b", re.I)
_KNOWN_HOLDER = re.compile(
    r"(?:The [Aa]uthors?|[Aa]uthors?|Springer|Elsevier|Wiley|WILEY|The Royal Society|"
    r"The Economic History Association|Ivyspring|RSNA|American|Association for)\b")
_ABBREVIATION = re.compile(r"(?:B\.V|Inc|Co|Ltd|S\.A|U\.S|U\.K|L\.L\.C|et al)\.$", re.I)


def _notice_tail(tail):
    tail = tail.strip()
    if not tail:  # An otherwise standalone terminal copyright symbol.
        return True
    clauses, position = [], 0
    for match in re.finditer(r'(?<=[.!?])(?:\s+|(?=All rights reserved))(?=[A-Z])', tail):
        if (_ABBREVIATION.search(tail[:match.start()]) and
                not _RIGHTS.match(tail[match.end():])):
            continue
        clauses.append(tail[position:match.start()])
        position = match.end()
    clauses.append(tail[position:])
    holder = clauses[0]
    year = _YEAR.match(holder)
    if year:
        holder = holder[year.end():].strip()
    else:
        # MTI exports also have the year after the holder, or omit it entirely.
        if not re.search(r'\b(?:19|20)\d{2}\b', holder) and not _KNOWN_HOLDER.match(holder):
            return False
    holder = re.sub(r'^by\s+', '', holder)
    if len(holder) > 220 or len(holder.split()) > 35 or _PROSE.search(holder):
        return False
    if holder and not (holder[0].isupper() or re.match(r'(?:the [A-Z]|the authors?\b|authors?\b)', holder)):
        return False
    if any(character in holder for character in '!?;©“”"'):
        return False
    for clause in clauses[1:]:
        if not _RIGHTS.fullmatch(clause):
            return False
        # Separate publisher credits from narrative uses of 'published'.
        if ('published' in clause.lower() and not clause.lower().startswith('this article')
                and _PROSE.search(clause)):
            return False
    return True


def strip_copyright(text):
    """Remove recognized terminal copyright notices at sentence boundaries."""
    text = re.sub(r'(?<=[.!?])\s+Copyright of the Academy of Management, all rights reserved\.\s*$', '', text)
    for match in _COPYRIGHT.finditer(text):
        before = text[:match.start()]
        if before.strip() and before.rstrip()[-1] not in '.!?)]':
            continue
        if _notice_tail(text[match.end():]):
            return before.rstrip()
    return text


_LEADING_EM_DASH = re.compile(r'^\s*—(?:\s*—)*\s*')


def strip_leading_em_dash(text):
    """Remove initial U+2014 separators and adjacent boundary whitespace only."""
    return _LEADING_EM_DASH.sub('', text)


@dataclass(frozen=True)
class CleaningResult:
    text: str
    copyright_removed: bool = False
    headings_removed: bool = False
    leading_em_dash_removed: bool = False


def clean_abstract_with_audit(text):
    """Return cleaned text and removal flags; see clean_abstract for inputs."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return CleaningResult('')
    if not isinstance(text, str):
        raise TypeError('abstract must be str, None, or float NaN')
    if not text.strip() or text.strip() == '[No abstract available]':
        return CleaningResult('')
    copyright_removed = headings_removed = leading_em_dash_removed = False
    # Repeat because a removal can expose another heading or notice.
    while True:
        copyright_free = strip_copyright(text)
        heading_free = strip_headings(copyright_free)
        cleaned = strip_leading_em_dash(heading_free)
        copyright_removed |= copyright_free != text
        headings_removed |= heading_free != copyright_free
        leading_em_dash_removed |= cleaned != heading_free
        if cleaned == text:
            return CleaningResult(text, copyright_removed, headings_removed, leading_em_dash_removed)
        if len(cleaned) >= len(text):
            raise AssertionError('cleaning must only remove text')
        text = cleaned


def clean_abstract(text):
    """Return cleaned text, preserving retained Unicode characters."""
    return clean_abstract_with_audit(text).text
