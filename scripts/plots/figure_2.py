import textwrap
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, FancyArrowPatch
from matplotlib.path import Path as MplPath

from config import ROOT
from utils.figure_style import style


def draw(data, path):
    style()
    values = data.set_index('metric').value
    n = int(values['abstracts'])
    hits = int(values['em_positive'])
    changes = {
        'text-3': f"{int(values['classified_sources']):,} journals retained",
        'text-6': f"{int(values['classified_records_2019_2026']):,} unique papers",
        'text-9': f"No abstract: {int(values['without_abstract']):,}",
        'text-10': f"Corrections or errata: {int(values['correction_prefix']):,}",
        'text-11': f'{n:,} abstracts',
        'text-12': 'Final analytical corpus',
        'text-15': f'Classify all {n:,} abstracts',
        'text-16': 'Em dash present: ≥1 “—”',
        'text-17': 'Otherwise: em dash absent',
        'text-18': f'{hits:,} positive ({100 * hits / n:.2f}%)',
        'text-19': 'Validation sample',
        'text-20': 'Manual validation',
        'text-21': f"{int(values['validation_reviewed'])} abstracts reviewed",
        'text-22': 'Against publisher webpages',
        'text-23': f"{int(values['validation_agreement'])}/{int(values['validation_reviewed'])} agree ({100 * values['validation_agreement'] / values['validation_reviewed']:.2f}%)",
        'text-31': f"2019–2022 ({100 * values['n_baseline'] / n:.0f}% of corpus)",
        'NlzVDXdYi95rhsZhDBUY-1': f"versus 2023–2026 ({100 * values['n_post'] / n:.0f}% of corpus)",
        'text-34': f"{int(values['areas']):,} areas (covering {values['area_share']:.1f}% of corpus)",
        'text-35': f"{int(values['publishers']):,} publishers ({values['publisher_share']:.1f}% of corpus)",
    }
    source = ROOT / 'assets' / 'workflow.drawio'
    tree = ET.parse(source)
    cells = {c.get('id'): c for c in tree.getroot().find('diagram').iter('mxCell')}
    for key, value in changes.items():
        cells[key].set('value', value)

    def attrs(cell):
        return dict(part.split('=', 1) for part in cell.get('style', '').split(';') if '=' in part)

    def geometry(key):
        cell = cells[key]
        geom = cell.find('mxGeometry')
        if geom is None:
            return 0, 0, 0, 0
        x, y, w, h = [float(geom.get(k, 0)) for k in ['x', 'y', 'width', 'height']]
        parent = cell.get('parent')
        if parent not in [None, '0', '1']:
            px, py, _, _ = geometry(parent)
            x, y = x + px, y + py
        return x, y, w, h

    fig, ax = plt.subplots(figsize=(15, 8))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, 1500), ylim=(800, 0))
    ax.set_axis_off()
    for key, cell in cells.items():
        settings = attrs(cell)
        if cell.get('vertex') == '1':
            x, y, w, h = geometry(key)
            if cell.get('value'):
                font = float(settings.get('fontSize', 21)) * .72
                value = cell.get('value')
                lines = textwrap.fill(value, width=max(12, int(w / (font * .65))),
                                      break_long_words=False, break_on_hyphens=False)
                ax.text(x, y + h / 2, lines, fontsize=font,
                        fontfamily=settings.get('fontFamily', 'TeX Gyre Pagella'),
                        fontweight='bold' if settings.get('fontStyle') == '1' else 'normal',
                        color=settings.get('fontColor', '#182832'), va='center', ha='left',
                        linespacing=1.12)
            elif settings.get('fillColor', 'none') != 'none' and min(w, h) > 5:
                shape = (Ellipse((x + w / 2, y + h / 2), w, h)
                         if cell.get('style', '').startswith('ellipse;') else
                         FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=9'))
                shape.set(
                    facecolor=settings.get('fillColor', 'white'),
                    edgecolor=settings.get('strokeColor', 'none'),
                    linewidth=float(settings.get('strokeWidth', 1)) * .72)
                ax.add_patch(shape)
        if cell.get('edge') == '1':
            geom = cell.find('mxGeometry')
            parent = cell.get('parent')
            px, py, _, _ = geometry(parent) if parent in cells else (0, 0, 0, 0)
            points = []
            for endpoint, kind in [('source', 'exit'), ('target', 'entry')]:
                target = cell.get(endpoint)
                if target:
                    x, y, w, h = geometry(target)
                    point = (x + w * float(settings.get(kind + 'X', .5)),
                             y + h * float(settings.get(kind + 'Y', .5)))
                else:
                    p = geom.find(f"mxPoint[@as='{endpoint}Point']")
                    point = (px + float(p.get('x')), py + float(p.get('y')))
                if endpoint == 'target':
                    points.extend((px + float(p.get('x')), py + float(p.get('y')))
                                  for p in geom.findall('Array/mxPoint'))
                points.append(point)
            ax.add_patch(FancyArrowPatch(path=MplPath(points),
                arrowstyle='-|>' if settings.get('endArrow') == 'block' else '-',
                mutation_scale=8, color=settings.get('strokeColor', '#647580'),
                linewidth=float(settings.get('strokeWidth', 1)) * .72,
                linestyle=(0, (6, 5)) if settings.get('dashed') == '1' else '-'))
    fig.savefig(path, dpi=300, facecolor='white')
    plt.close(fig)
