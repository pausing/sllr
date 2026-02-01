"""
Management reports and dashboard data export for SLLR.
"""
import csv
from pathlib import Path
from typing import Any

from sllr.config import PROJECT_ROOT
from sllr.duplicate_detection import find_duplicates, find_near_duplicates
from sllr.kpi import compute_kpis, kpi_summary_text
from sllr.loaders import load_lessons_master
from sllr.validation import validate_lessons_file


def generate_validation_report(output_path: Path | None = None) -> str:
    """Run validation and write a validation report (text)."""
    rows = load_lessons_master()
    issues = validate_lessons_file(rows)
    path = output_path or (PROJECT_ROOT / "reports" / "validation_report.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "SLLR Validation Report",
        "======================",
        f"Total rows: {len(rows)}",
        f"Rows with errors: {len(issues)}",
        "",
    ]
    for row_num, errs in issues:
        lines.append(f"Row {row_num}:")
        for e in errs:
            lines.append(f"  - {e}")
        lines.append("")
    content = "\n".join(lines)
    path.write_text(content, encoding="utf-8")
    return content


def generate_duplicates_report(output_path: Path | None = None) -> str:
    """List exact and near-duplicates in a text report."""
    rows = load_lessons_master()
    exact = find_duplicates(rows)
    near = find_near_duplicates(rows)
    path = output_path or (PROJECT_ROOT / "reports" / "duplicates_report.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "SLLR Duplicates Report",
        "======================",
        f"Exact duplicate groups: {len(exact)}",
        f"Near-duplicate pairs (by title similarity): {len(near)}",
        "",
    ]
    for i, group in enumerate(exact, 1):
        lines.append(f"Exact group {i} ({len(group)} lessons):")
        for r in group:
            lines.append(f"  - [{r.get('Lesson ID')}] {r.get('Title', '')[:60]}...")
        lines.append("")
    lines.append("--- Near duplicates (top 20 by similarity) ---")
    for r1, r2, sim in near[:20]:
        lines.append(f"  Sim={sim}: [{r1.get('Lesson ID')}] vs [{r2.get('Lesson ID')}]")
        lines.append(f"    A: {str(r1.get('Title', ''))[:70]}")
        lines.append(f"    B: {str(r2.get('Title', ''))[:70]}")
    content = "\n".join(lines)
    path.write_text(content, encoding="utf-8")
    return content


def generate_kpi_report(output_path: Path | None = None) -> str:
    """Write KPI summary to a text file."""
    content = kpi_summary_text()
    path = output_path or (PROJECT_ROOT / "reports" / "kpi_report.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return content


def export_dashboard_csv(output_path: Path | None = None) -> Path:
    """
    Export a flat CSV suitable for Power BI: lessons plus computed flags.
    Adds columns: Is_Embedded, Reuse_Count_Num, Validation_Errors.
    """
    rows = load_lessons_master()
    from sllr.validation import validate_lesson
    from sllr.loaders import load_all_references
    refs = load_all_references()
    fieldnames = list(rows[0].keys()) if rows else []
    extra = ["Is_Embedded", "Reuse_Count_Num", "Validation_Errors"]
    for c in extra:
        if c not in fieldnames:
            fieldnames.append(c)
    out_rows: list[dict[str, Any]] = []
    for r in rows:
        row = dict(r)
        row["Is_Embedded"] = 1 if (row.get("Status") or "").strip() == "Embedded" else 0
        try:
            row["Reuse_Count_Num"] = int(float(str(row.get("Reuse Count") or 0)))
        except (ValueError, TypeError):
            row["Reuse_Count_Num"] = 0
        errs = validate_lesson(row, refs)
        row["Validation_Errors"] = "; ".join(errs) if errs else ""
        out_rows.append(row)
    path = output_path or (PROJECT_ROOT / "reports" / "dashboard_export.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)
    return path


def run_all_reports(reports_dir: Path | None = None) -> dict[str, str]:
    """Run validation, duplicates, and KPI reports; return paths/content."""
    base = reports_dir or (PROJECT_ROOT / "reports")
    base.mkdir(parents=True, exist_ok=True)
    return {
        "validation": generate_validation_report(base / "validation_report.txt"),
        "duplicates": generate_duplicates_report(base / "duplicates_report.txt"),
        "kpi": generate_kpi_report(base / "kpi_report.txt"),
        "dashboard_csv": str(export_dashboard_csv(base / "dashboard_export.csv")),
    }
