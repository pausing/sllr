#!/usr/bin/env python3
"""
Print KPI summary to console.
Usage: python scripts/kpi_summary.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sllr.kpi import kpi_summary_text


def main() -> int:
    print(kpi_summary_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
