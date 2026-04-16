"""
Hlavní orchestrace — spustí celou EDA pipeline jedním příkazem.

Použití:
    python scripts/main_trigger.py          # spustí vše (01–04)
    python scripts/main_trigger.py 02 04    # spustí jen vybrané kroky
"""

import importlib
import sys
import time
from pathlib import Path

# Přidej scripts/ do sys.path, aby importy uvnitř modulů fungovaly
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Moduly s číslem v názvu — importujeme přes importlib
_mod01 = importlib.import_module("01_eda_summary")
_mod02 = importlib.import_module("02_visualizations")
_mod03 = importlib.import_module("03_geo_map")
_mod04 = importlib.import_module("04_treemap_sankey")

STEPS = {
    "01": ("EDA Summary", _mod01.run_eda),
    "02": ("Visualizations (bar, heatmap, ridge)", _mod02.run),
    "03": ("Geo Choropleth Maps", _mod03.run),
    "04": ("Treemap & Sankey", _mod04.run),
}


def main():
    # Vyber kroky z CLI argumentů, nebo spusť vše
    selected = sys.argv[1:] if len(sys.argv) > 1 else list(STEPS)

    for key in selected:
        if key not in STEPS:
            print(f"[ERROR] Unknown step '{key}'. Available: {', '.join(STEPS)}")
            sys.exit(1)

    print("=" * 60)
    print("Pracuj_all_viz — Full Pipeline")
    print("=" * 60)

    failed = []
    for key in selected:
        label, func = STEPS[key]
        print(f"\n>>> [{key}] {label}")
        t0 = time.perf_counter()
        try:
            func()
            elapsed = time.perf_counter() - t0
            print(f"    OK  ({elapsed:.1f}s)")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            print(f"    FAIL ({elapsed:.1f}s) — {exc}")
            failed.append(key)

    # Souhrn
    print("\n" + "=" * 60)
    if failed:
        print(f"Done with errors. Failed steps: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"All {len(selected)} steps completed successfully.")


if __name__ == "__main__":
    main()
