"""
SLLR Streamlit App — Structured Lessons Learned Registry.
Run from project root: streamlit run app.py
"""
import sys
from pathlib import Path

# Ensure src is on path when running from project root
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import pandas as pd
from datetime import datetime

from sllr.config import LESSON_SCHEMA
from sllr.loaders import load_lessons_master, load_all_references, save_lessons_master
from sllr.validation import validate_lesson, validate_lessons_file
from sllr.duplicate_detection import find_duplicates, find_near_duplicates
from sllr.kpi import compute_kpis, kpi_summary_text
from sllr.reports import run_all_reports
from sllr.export_pdf import build_pdf, REPORTLAB_AVAILABLE
from sllr.export_html import build_html
from sllr.embed_report import get_report_html, DEFAULT_HEIGHT

st.set_page_config(
    page_title="SLLR — Lessons Learned Registry",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
st.sidebar.title("📋 SLLR")
st.sidebar.caption("Structured Lessons Learned Registry")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Browse lessons", "Add lesson", "Approve / Update status", "Validation", "Duplicates", "View report", "Export", "Reports"],
    label_visibility="collapsed",
)

# Shared data loaders (cached)
@st.cache_data(ttl=60)
def get_lessons():
    return load_lessons_master()

@st.cache_data(ttl=60)
def get_refs():
    return load_all_references()

def clear_caches():
    get_lessons.clear()
    get_refs.clear()

# ---------- Dashboard ----------
if page == "Dashboard":
    st.title("Dashboard")
    lessons = get_lessons()
    kpis = compute_kpis(lessons)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total lessons", kpis["total_lessons"])
    with col2:
        st.metric("% Embedded", f"{kpis['pct_embedded']}%")
    with col3:
        st.metric("Lessons reused", kpis["lessons_reused"])
    with col4:
        avg = kpis["capture_to_approval_days_avg"]
        st.metric("Avg capture→approval (days)", avg if avg is not None else "—")
    with col5:
        st.metric("Repeated issues", kpis["repeated_issues_count"])

    def _bar_df(d: dict) -> pd.DataFrame:
        if not d:
            return pd.DataFrame()
        return pd.DataFrame({"Count": list(d.values())}, index=list(d.keys()))

    st.subheader("By status")
    if kpis["by_status"]:
        st.bar_chart(_bar_df(kpis["by_status"]))
    else:
        st.info("No lessons yet.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("By discipline")
        if kpis["by_discipline"]:
            st.bar_chart(_bar_df(kpis["by_discipline"]))
        else:
            st.info("No data.")
    with col_b:
        st.subheader("By failure type")
        if kpis["by_failure_type"]:
            st.bar_chart(_bar_df(kpis["by_failure_type"]))
        else:
            st.info("No data.")

# ---------- Browse lessons ----------
elif page == "Browse lessons":
    st.title("Browse lessons")
    lessons = get_lessons()
    if not lessons:
        st.info("No lessons in the registry yet. Add one from **Add lesson**.")
        st.stop()

    df = pd.DataFrame(lessons)
    refs = get_refs()

    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            disciplines = [""] + (refs.get("disciplines") or [])
            sel_discipline = st.selectbox("Discipline", disciplines)
        with c2:
            phases = [""] + (refs.get("phases") or [])
            sel_phase = st.selectbox("Project phase", phases)
        with c3:
            statuses = [""] + (refs.get("statuses") or [])
            sel_status = st.selectbox("Status", statuses)

    mask = pd.Series([True] * len(df))
    if "Discipline" in df.columns and sel_discipline:
        mask &= df["Discipline"] == sel_discipline
    if "Project Phase" in df.columns and sel_phase:
        mask &= df["Project Phase"] == sel_phase
    if "Status" in df.columns and sel_status:
        mask &= df["Status"] == sel_status
    df = df[mask]

    st.dataframe(df, width="stretch", hide_index=True)

    # Update status (Draft → Approved → Embedded)
    st.divider()
    st.subheader("Update lesson status")
    st.caption("Move a lesson along the lifecycle: **Draft** → **Approved** → **Embedded**.")
    lesson_options = [f"{r.get('Lesson ID', '')} — {str(r.get('Title', ''))[:60]}…" if len(str(r.get('Title', ''))) > 60 else f"{r.get('Lesson ID', '')} — {r.get('Title', '')}" for r in lessons]
    lesson_ids = [r.get("Lesson ID", "") for r in lessons]
    status_options = refs.get("statuses") or ["Draft", "Approved", "Embedded"]
    choice = st.selectbox("Select lesson", range(len(lesson_options)), format_func=lambda i: lesson_options[i], key="browse_status_lesson")
    new_status = st.selectbox("New status", status_options, key="browse_new_status")
    if st.button("Update status", key="browse_update_btn"):
        lid = lesson_ids[choice]
        now = datetime.now().strftime("%Y-%m-%d")
        updated = []
        for r in lessons:
            if r.get("Lesson ID") == lid:
                r = dict(r)
                r["Status"] = new_status
                r["Modified Date"] = now
            updated.append(r)
        save_lessons_master(updated, fieldnames=list(LESSON_SCHEMA.keys()))
        clear_caches()
        st.success(f"**{lid}** set to **{new_status}**.")
        st.rerun()

# ---------- Add lesson ----------
elif page == "Add lesson":
    st.title("Add lesson")
    refs = get_refs()
    lessons = get_lessons()
    fieldnames = list(LESSON_SCHEMA.keys())

    # Next ID suggestion
    existing_ids = {r.get("Lesson ID", "") for r in lessons if r.get("Lesson ID")}
    next_id = "LL-001"
    for i in range(1, 1000):
        cand = f"LL-{i:03d}"
        if cand not in existing_ids:
            next_id = cand
            break

    with st.form("add_lesson_form"):
        st.subheader("New lesson")
        lesson_id = st.text_input("Lesson ID", value=next_id)
        title = st.text_input("Title (one-line summary)", max_chars=200)
        category = st.selectbox("Category", refs.get("categories") or [""])
        sub_category = st.text_input("Sub-category")
        discipline = st.selectbox("Discipline", refs.get("disciplines") or [""])
        project_phase = st.selectbox("Project phase", refs.get("phases") or [""])
        failure_type = st.selectbox("Failure type", refs.get("failure_types") or [""])
        root_cause = st.text_area("Root cause")
        what_happened = st.text_area("What happened")
        impact = st.text_input("Impact (e.g. Cost; Schedule)")
        lesson_learned = st.text_area("Lesson learned (single sentence)", max_chars=500)
        recommendation = st.text_area("Recommendation")
        applicability = st.text_input("Applicability (optional)")
        keywords = st.text_input("Keywords (optional)")
        status = st.selectbox("Status", refs.get("statuses") or [""])
        owner = st.text_input("Owner")
        reuse_count = st.number_input("Reuse count", min_value=0, value=0, step=1)

        submitted = st.form_submit_button("Save lesson")
        if submitted:
            now = datetime.now().strftime("%Y-%m-%d")
            row = {
                "Lesson ID": lesson_id,
                "Title": title,
                "Category": category,
                "Sub-category": sub_category,
                "Discipline": discipline,
                "Project Phase": project_phase,
                "Failure Type": failure_type,
                "Root Cause": root_cause,
                "What Happened": what_happened,
                "Impact": impact,
                "Lesson Learned": lesson_learned,
                "Recommendation": recommendation,
                "Applicability": applicability or "",
                "Keywords": keywords or "",
                "Status": status,
                "Owner": owner,
                "Created Date": now,
                "Modified Date": now,
                "Reuse Count": str(reuse_count),
            }
            errs = validate_lesson(row, refs)
            if errs:
                for e in errs:
                    st.error(e)
            else:
                new_rows = lessons + [row]
                save_lessons_master(new_rows, fieldnames=fieldnames)
                clear_caches()
                st.success("Lesson saved.")
                st.balloons()

# ---------- Approve / Update status ----------
elif page == "Approve / Update status":
    st.title("Approve / Update status")
    st.markdown(
        "Move lessons along the lifecycle: **Draft** → **Approved** → **Embedded**. "
        "Select a lesson and choose the new status, then click **Update status**."
    )
    lessons = get_lessons()
    if not lessons:
        st.info("No lessons in the registry yet. Add one from **Add lesson**.")
        st.stop()

    refs = get_refs()
    status_options = refs.get("statuses") or ["Draft", "Approved", "Embedded"]
    lesson_options = [
        f"{r.get('Lesson ID', '')} — {str(r.get('Title', ''))[:70]}{'…' if len(str(r.get('Title', ''))) > 70 else ''} [{r.get('Status', '')}]"
        for r in lessons
    ]
    lesson_ids = [r.get("Lesson ID", "") for r in lessons]

    with st.form("update_status_form"):
        idx = st.selectbox(
            "Select lesson",
            range(len(lesson_options)),
            format_func=lambda i: lesson_options[i],
            key="approve_lesson",
        )
        new_status = st.selectbox("New status", status_options, key="approve_new_status")
        submitted = st.form_submit_button("Update status")
        if submitted:
            lid = lesson_ids[idx]
            now = datetime.now().strftime("%Y-%m-%d")
            updated = []
            for r in lessons:
                r = dict(r)
                if r.get("Lesson ID") == lid:
                    r["Status"] = new_status
                    r["Modified Date"] = now
                updated.append(r)
            save_lessons_master(updated, fieldnames=list(LESSON_SCHEMA.keys()))
            clear_caches()
            st.success(f"**{lid}** is now **{new_status}**.")
            st.rerun()

    # Quick filter: show Draft lessons to approve
    draft_lessons = [r for r in lessons if (r.get("Status") or "").strip() == "Draft"]
    if draft_lessons:
        st.subheader("Draft lessons (ready to approve)")
        st.dataframe(
            pd.DataFrame(draft_lessons)[["Lesson ID", "Title", "Status", "Owner"]],
            width="stretch",
            hide_index=True,
        )

# ---------- Validation ----------
elif page == "Validation":
    st.title("Validation")
    lessons = get_lessons()
    if not lessons:
        st.info("No lessons to validate.")
        st.stop()

    issues = validate_lessons_file(lessons)
    if not issues:
        st.success(f"All {len(lessons)} rows passed validation.")
        st.stop()

    st.warning(f"{len(issues)} row(s) with errors.")
    for row_num, errs in issues:
        st.markdown(f"**Row {row_num}**")
        for e in errs:
            st.markdown(f"- {e}")
        st.divider()

# ---------- Duplicates ----------
elif page == "Duplicates":
    st.title("Duplicates")
    lessons = get_lessons()
    if len(lessons) < 2:
        st.info("Need at least 2 lessons to check for duplicates.")
        st.stop()

    exact = find_duplicates(lessons)
    near = find_near_duplicates(lessons)

    st.subheader("Exact duplicates")
    if not exact:
        st.success("No exact duplicate groups.")
    else:
        for i, group in enumerate(exact, 1):
            st.markdown(f"**Group {i}** ({len(group)} lessons)")
            for r in group:
                st.caption(f"[{r.get('Lesson ID')}] {str(r.get('Title', ''))[:80]}")
            st.divider()

    st.subheader("Near duplicates (by title similarity)")
    if not near:
        st.success("No near-duplicate pairs above threshold.")
    else:
        for r1, r2, sim in near[:30]:
            st.markdown(f"Similarity **{sim:.0%}**")
            st.caption(f"A: [{r1.get('Lesson ID')}] {str(r1.get('Title', ''))[:70]}")
            st.caption(f"B: [{r2.get('Lesson ID')}] {str(r2.get('Title', ''))[:70]}")
            st.divider()

# ---------- View report (embedded HTML) ----------
elif page == "View report":
    st.title("View report")
    st.caption("HTML report with expandable cards and filters, embedded in the app.")
    lessons = get_lessons()
    if not lessons:
        st.info("No lessons to show. Add lessons from **Add lesson** or **Browse lessons**.")
        st.stop()
    html = get_report_html(lessons)
    st.components.v1.html(html, height=DEFAULT_HEIGHT, scrolling=True)

# ---------- Export ----------
elif page == "Export":
    st.title("Export")
    st.caption("Generate PDF (phase → category, page breaks between categories) or HTML (expandable cards with filters).")
    lessons = get_lessons()
    if not lessons:
        st.info("No lessons to export. Add lessons first.")
        st.stop()

    pdf_path = ROOT / "reports" / "lessons_learned.pdf"
    html_path = ROOT / "reports" / "lessons_learned.html"

    col_pdf, col_html = st.columns(2)
    with col_pdf:
        st.subheader("PDF")
        st.markdown("One section per **Phase**; within each phase, content ordered by **Category** → **Discipline** → **Sub-category**, with a **page break between categories**.")
        if REPORTLAB_AVAILABLE:
            if st.button("Generate PDF", key="export_pdf_btn"):
                with st.spinner("Building PDF…"):
                    try:
                        build_pdf(lessons, pdf_path)
                        clear_caches()
                        st.success(f"Saved: `{pdf_path}`")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            if pdf_path.exists():
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f.read(), file_name="lessons_learned.pdf", mime="application/pdf", key="dl_pdf")
        else:
            st.warning("Install **reportlab** for PDF export: `pip install reportlab`")

    with col_html:
        st.subheader("HTML")
        st.markdown("Single HTML file with **expandable cards** and **filters** (Phase, Category, Discipline, Status). Open in any browser; no server needed.")
        if st.button("Generate HTML", key="export_html_btn"):
            with st.spinner("Building HTML…"):
                try:
                    build_html(lessons, html_path)
                    clear_caches()
                    st.success(f"Saved: `{html_path}`")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        if html_path.exists():
            st.download_button(
                "Download HTML",
                html_path.read_bytes(),
                file_name="lessons_learned.html",
                mime="text/html",
                key="dl_html",
            )

    st.divider()
    st.markdown("**Output folder:** `reports/` — PDF: `lessons_learned.pdf`, HTML: `lessons_learned.html`")

# ---------- Reports ----------
elif page == "Reports":
    st.title("Reports")
    st.caption("Generate validation, duplicates, KPI, and dashboard CSV reports.")
    if st.button("Generate all reports"):
        with st.spinner("Generating reports…"):
            try:
                result = run_all_reports(ROOT / "reports")
                clear_caches()
                st.success("Reports generated.")
                st.json({k: "(see file)" for k in result})
                st.info("Outputs are in the `reports/` folder: validation_report.txt, duplicates_report.txt, kpi_report.txt, dashboard_export.csv")
            except Exception as e:
                st.error(str(e))

    st.subheader("KPI summary (live)")
    st.text(kpi_summary_text())
