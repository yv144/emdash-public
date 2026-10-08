from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


def style():
    plt.rcdefaults()
    folder = Path(__file__).resolve().parents[2] / "assets" / "fonts"
    for path in folder.glob("texgyrepagella-*.otf"):
        font_manager.fontManager.addfont(path)
