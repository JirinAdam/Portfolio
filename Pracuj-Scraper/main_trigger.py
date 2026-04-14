"""main_trigger.py — Run the full Pracuj.pl scraping pipeline.

Steps:
  1. url_list_search2.0.py       — scrape listing URLs from pracuj.pl
  2. detail_scraper2.0.py        — parallel scrape of each listing → job_database.db
  3. db_cleaner/database_cleaner.py — clean & normalise (interactive confirmations)
  4. nerds_db_filter.py          — filter IT roles → nerd_jobs.db
  5. snapshot_history.py         — append monthly CSV snapshots

Usage:
  python main_trigger.py                 # full pipeline
  python main_trigger.py --skip-scrape   # skip steps 1+2, run cleanup/filter/snapshot only
  python main_trigger.py --workers 64    # custom worker count for parallel scraper
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.absolute()

# UTF-8 env so emoji output from db_cleaner doesn't crash on Windows cp1252
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run_step(step_num: int, total: int, label: str, cmd: list[str]) -> None:
    """Run a single pipeline step, abort on failure."""
    print(f"\n{'=' * 80}")
    print(f"  STEP {step_num}/{total}: {label}")
    print(f"{'=' * 80}\n")

    result = subprocess.run(cmd, env=ENV)

    if result.returncode != 0:
        print(f"\nSTEP {step_num} FAILED (exit code {result.returncode}). Pipeline aborted.")
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full Pracuj.pl scraping pipeline.")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Skip steps 1+2 (URL scrape + detail scrape). "
                             "Useful for re-running cleanup/filter/snapshot on existing DB.")
    parser.add_argument("--workers", type=int, default=32,
                        help="Number of parallel workers for detail_scraper2.0.py (default: 32)")
    args = parser.parse_args()

    steps: list[tuple[str, list[str]]] = []

    if not args.skip_scrape:
        steps.append((
            "Scrape listing URLs",
            [sys.executable, str(ROOT / "url_list_search2.0.py")],
        ))
        steps.append((
            f"Parallel detail scraper ({args.workers} workers)",
            [sys.executable, str(ROOT / "detail_scraper2.0.py"),
             "--workers", str(args.workers)],
        ))

    steps.append((
        "Database cleaner (interactive)",
        [sys.executable, str(ROOT / "db_cleaner" / "database_cleaner.py")],
    ))
    steps.append((
        "Nerd jobs filter",
        [sys.executable, str(ROOT / "nerds_db_filter.py")],
    ))
    steps.append((
        "Snapshot history (CSV)",
        [sys.executable, str(ROOT / "snapshot_history.py")],
    ))

    total = len(steps)
    print(f"\nPipeline: {total} steps" +
          (" (scraping skipped)" if args.skip_scrape else ""))

    for i, (label, cmd) in enumerate(steps, 1):
        run_step(i, total, label, cmd)

    print(f"\n{'=' * 80}")
    print("  PIPELINE COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
