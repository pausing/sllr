"""
KPI computation for the Lessons Learned Registry.
"""
from collections import defaultdict
from datetime import datetime
from typing import Any

from sllr.loaders import load_lessons_master


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
    rows = rows or load_lessons_master()
    if not rows:
        return {
            "total_lessons": 0,
            "pct_embedded": 0.0,
            "lessons_embedded": 0,
            "lessons_reused": 0,
            "total_reuse_count": 0,
            "repeated_issues_count": 0,
            "capture_to_approval_days_avg": None,
            "by_status": {},
            "by_discipline": {},
            "by_failure_type": {},
        }

    total = len(rows)
    by_status = defaultdict(int)
    embedded = 0
    total_reuse = 0
    approval_times = []

    for r in rows:
        status = (r.get("Status") or "").strip()
        by_status[status] += 1
        if status == "Embedded":
            embedded += 1
        total_reuse += _to_int(r.get("Reuse Count"))

        created = _parse_date(r.get("Created Date"))
        modified = _parse_date(r.get("Modified Date"))
        if created and modified and status == "Approved":
            delta = (modified - created).days
            if delta >= 0:
                approval_times.append(delta)

    pct_embedded = (embedded / total * 100) if total else 0.0
    avg_approval = (
        round(sum(approval_times) / len(approval_times), 1) if approval_times else None
    )

    # Repeated issues: count lessons that share same (Discipline, Failure Type, Root Cause) pattern
    pattern_count: dict[str, int] = defaultdict(int)
    for r in rows:
        key = (
            (r.get("Discipline") or "").strip(),
            (r.get("Failure Type") or "").strip(),
            (r.get("Root Cause") or "").strip()[:100],
        )
        pattern_count[str(key)] += 1
    repeated_issues = sum(1 for c in pattern_count.values() if c > 1)

    by_discipline = defaultdict(int)
    by_failure_type = defaultdict(int)
    for r in rows:
        by_discipline[(r.get("Discipline") or "").strip() or "Unknown"] += 1
        by_failure_type[(r.get("Failure Type") or "").strip() or "Unknown"] += 1

    return {
        "total_lessons": total,
        "pct_embedded": round(pct_embedded, 1),
        "lessons_embedded": embedded,
        "lessons_reused": sum(1 for r in rows if _to_int(r.get("Reuse Count", 0)) > 0),
        "total_reuse_count": total_reuse,
        "repeated_issues_count": repeated_issues,
        "capture_to_approval_days_avg": avg_approval,
        "by_status": dict(by_status),
        "by_discipline": dict(by_discipline),
        "by_failure_type": dict(by_failure_type),
    }


def kpi_summary_text(kpis: dict[str, Any] | None = None) -> str:
    """Format KPIs as a short text summary."""
    kpis = kpis or compute_kpis()
    lines = [
        "--- SLLR KPI Summary ---",
        f"Total lessons: {kpis['total_lessons']}",
        f"% Lessons Embedded: {kpis['pct_embedded']}%",
        f"Lessons with reuse: {kpis['lessons_reused']} (total reuse count: {kpis['total_reuse_count']})",
        f"Repeated issues (same discipline/failure/root cause): {kpis['repeated_issues_count']}",
        f"Avg capture-to-approval (days): {kpis['capture_to_approval_days_avg'] or 'N/A'}",
        "By Status: " + ", ".join(f"{k}={v}" for k, v in kpis["by_status"].items()),
    ]
    return "\n".join(lines)
