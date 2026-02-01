#!/usr/bin/env python3
"""
Generate all SLLR reports: validation, duplicates, KPI, and dashboard CSV.
Usage: python scripts/run_reports.py [reports_dir]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sllr.reports import run_all_reports


def main() -> int:
    reports_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    result = run_all_reports(reports_dir)
    print("Reports generated:")
    for name, path_or_content in result.items():
        if name == "dashboard_csv":
            print(f"  {name}: {path_or_content}")
        else:
            print(f"  {name}: (see file; preview below)")
            print(path_or_content[:500] + "..." if len(str(path_or_content)) > 500 else path_or_content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
