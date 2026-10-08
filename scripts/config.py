import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def input_path(name):
    value = os.getenv(name)
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


DATASET_PATH = input_path("DATASET_PATH")
SOURCE_LIST_PATH = input_path("SOURCE_LIST_PATH")
PREPARED = ROOT / ".cache" / "articles.csv"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
DATA = ROOT / "data"
BASELINE_YEARS = range(2019, 2023)
COMPARISON_YEAR = 2026
MARKERS = {
    "em": "Em dash (—)",
    "en_numeric": "En dash between digits (–)",
    "en_nonnumeric": "Other en dash (–)",
    "curly_apostrophe": "Curly apostrophe (’)",
    "curly_quote": "Opening curly quotation mark (“)",
    "semicolon": "Semicolon (;)",
    "degree_sign": "Degree sign (°)",
    "times_sign": "Multiplication sign (×)",
    "greek_alpha": "Greek alpha (α)",
}
