"""
Duplicate and near-duplicate detection for lessons learned.
"""
import re
from collections import defaultdict
from typing import Any

from sllr.loaders import load_lessons_master


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, remove punctuation for comparison."""
    if not text:
        return ""
    t = str(text).lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def lesson_signature(row: dict[str, Any]) -> str:
    """Build a comparable signature from key fields (Title + Root Cause + Lesson Learned)."""
    parts = [
        row.get("Title") or "",
        row.get("Root Cause") or "",
        row.get("Lesson Learned") or "",
    ]
    return normalize_text(" ".join(parts))


def find_duplicates(
    rows: list[dict[str, Any]] | None = None,
    key_fn: Any = lesson_signature,
) -> list[list[dict[str, Any]]]:
    """
    Find groups of lessons that share the same signature (exact duplicate content).
    Returns list of groups; each group is a list of row dicts that are duplicates.
    """
    if rows is None:
        rows = load_lessons_master()
    if not rows:
        return []

    by_sig: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        sig = key_fn(row)
        if sig:
            by_sig[sig].append(row)

    return [group for group in by_sig.values() if len(group) > 1]


def find_near_duplicates(
    rows: list[dict[str, Any]] | None = None,
    title_similarity_threshold: int = 3,
) -> list[tuple[dict[str, Any], dict[str, Any], float]]:
    """
    Find potential near-duplicates based on title word overlap (Jaccard-like).
    Returns list of (row1, row2, similarity_0_to_1).
    """
    if rows is None:
        rows = load_lessons_master()
    if len(rows) < 2:
        return []

    def token_set(s: str) -> set[str]:
        return set(normalize_text(s).split())

    titles = [(i, token_set(row.get("Title") or "")) for i, row in enumerate(rows)]
    pairs = []
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            idx_i, set_i = titles[i]
            idx_j, set_j = titles[j]
            if not set_i or not set_j:
                continue
            inter = len(set_i & set_j)
            union = len(set_i | set_j)
            sim = inter / union if union else 0
            if sim >= (title_similarity_threshold / 10.0):  # e.g. 0.3
                pairs.append((rows[idx_i], rows[idx_j], round(sim, 3)))

    return sorted(pairs, key=lambda x: -x[2])
