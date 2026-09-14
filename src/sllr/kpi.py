"""
KPI computation for the Lessons Learned Registry.
"""
from collections import defaultdict
from datetime import datetime
from typing import Any

from .loaders import load_lessons_master


def _parse_date(s: str | None) -> datetime | None:
    if not s or not str(s).strip():
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(s).strip()[:19], fmt)
        except ValueError:
            continue
    return None


def _to_int(v: Any) -> int:
    if v is None or v == "":
        return 0
    try:
        return int(float(str(v)))
    except (ValueError, TypeError):
        return 0


def compute_kpis(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Compute governance KPIs.
    - % Lessons Embedded
    - Lessons Reused (count / rate)
    - Repeated Issues (duplicate or near-duplicate indicators)
    - Capture-to-Approval Time (when dates available)
    """
    if rows is None:
        rows = load_lessons_master()
    if not rows:
        return {
            "total_lessons": 0,
            "repeated_issues_count": 0,
            "capture_to_approval_days_avg": None,
            "approved_count": 0,
            "implemented_count": 0,
            "pct_implemented": 0.0,
            "overdue_not_implemented_count": 0,
            "by_status": {},
            "by_category": {},
            "by_technical_block": {},
            "by_implementation_status": {},
        }

    total = len(rows)
    by_status = defaultdict(int)
    by_implementation_status = defaultdict(int)
    approval_times = []
    approved_rows = []
    today = datetime.now().date()

    for r in rows:
        status = (r.get("Status") or "").strip()
        by_status[status] += 1
        impl = (r.get("Implementation Status") or "").strip() or "Not Implemented"
        by_implementation_status[impl] += 1
        if status == "Approved":
            approved_rows.append(r)

        created = _parse_date(r.get("Created Date"))
        modified = _parse_date(r.get("Modified Date"))
        if created and modified and status == "Approved":
            delta = (modified - created).days
            if delta >= 0:
                approval_times.append(delta)

    avg_approval = (
        round(sum(approval_times) / len(approval_times), 1) if approval_times else None
    )

    # Implementation KPIs: among Approved lessons only
    implemented_count = sum(
        1 for r in approved_rows
        if (r.get("Implementation Status") or "").strip() == "Implemented"
    )
    approved_count = len(approved_rows)
    pct_implemented = (
        round(100.0 * implemented_count / approved_count, 1) if approved_count else 0.0
    )
    overdue_not_implemented_count = 0
    for r in approved_rows:
        if (r.get("Implementation Status") or "").strip() == "Implemented":
            continue
        due = _parse_date(r.get("Recommendation Due Date"))
        if due and due.date() < today:
            overdue_not_implemented_count += 1

    # Repeated issues: count lessons that share same (Technical Block, Category, Root Cause) pattern
    pattern_count: dict[str, int] = defaultdict(int)
    for r in rows:
        key = (
            (r.get("Technical Block") or "").strip(),
            (r.get("Category") or "").strip(),
            (r.get("Root Cause") or "").strip()[:100],
        )
        pattern_count[str(key)] += 1
    repeated_issues = sum(1 for c in pattern_count.values() if c > 1)

    by_category = defaultdict(int)
    by_technical_block = defaultdict(int)
    for r in rows:
        by_category[(r.get("Category") or "").strip() or "Unknown"] += 1
        by_technical_block[(r.get("Technical Block") or "").strip() or "Unknown"] += 1

    return {
        "total_lessons": total,
        "repeated_issues_count": repeated_issues,
        "capture_to_approval_days_avg": avg_approval,
        "approved_count": approved_count,
        "implemented_count": implemented_count,
        "pct_implemented": pct_implemented,
        "overdue_not_implemented_count": overdue_not_implemented_count,
        "by_status": dict(by_status),
        "by_category": dict(by_category),
        "by_technical_block": dict(by_technical_block),
        "by_implementation_status": dict(by_implementation_status),
    }


def kpi_summary_text(kpis: dict[str, Any] | None = None) -> str:
    """Format KPIs as a short text summary."""
    kpis = kpis or compute_kpis()
    lines = [
        "--- SLLR KPI Summary ---",
        f"Total lessons: {kpis['total_lessons']}",
        f"Repeated issues (same technical block/category/root cause): {kpis['repeated_issues_count']}",
        f"Avg capture-to-approval (days): {kpis['capture_to_approval_days_avg'] or 'N/A'}",
        f"Approved lessons: {kpis['approved_count']}",
        f"Recommendations implemented: {kpis['implemented_count']} ({kpis['pct_implemented']}% of approved)",
        f"Overdue (due date passed, not implemented): {kpis['overdue_not_implemented_count']}",
        "By Status: " + ", ".join(f"{k}={v}" for k, v in kpis["by_status"].items()),
        "By Implementation Status: " + ", ".join(f"{k}={v}" for k, v in kpis["by_implementation_status"].items()),
    ]
    return "\n".join(lines)
