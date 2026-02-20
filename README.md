# Structured Lessons Learned Registry (SLLR)

End-to-end methodology for capturing, classifying, storing, automating, and reusing lessons learned using **SharePoint**, **Python automation**, and **CSV databases**.

## Objective and Guiding Principles

- **Institutionalize learning** across projects.
- Lessons are **concise**, **structured**, **searchable**, and **embedded into standards**.
- Narrative reports without reuse are explicitly avoided.

## Repository Layout

```
lessonsLearned/
├── app.py                   # Streamlit app (run: streamlit run app.py)
├── data/                    # Data layer (CSV)
│   ├── lessons_master.csv   # One row per lesson
│   ├── categories.csv       # Development, Engineering, Procurement, Construction, O&M
│   ├── technical_blocks.csv  # Civil, HV & Grid, PV, BESS
│   ├── phases.csv           # Development, Pre-Execution, Construction, O&M
│   └── statuses.csv         # Draft, Approved
├── src/sllr/                # Logic layer (Python)
│   ├── config.py            # Paths and schema
│   ├── loaders.py           # Load reference CSVs and lessons master
│   ├── validation.py        # Validate against schema and vocabularies
│   ├── duplicate_detection.py
│   ├── kpi.py               # KPI computation
│   └── reports.py           # Management reports and dashboard export
├── scripts/                 # Entry points
│   ├── validate_lessons.py  # Validate lessons_master.csv
│   ├── run_reports.py       # Generate all reports
│   └── kpi_summary.py       # Print KPI summary
├── reports/                 # Output (generated)
│   ├── validation_report.txt
│   ├── duplicates_report.txt
│   ├── kpi_report.txt
│   └── dashboard_export.csv # For Power BI
└── docs/
    ├── SHAREPOINT_LIST_SCHEMA.md
    ├── POWER_BI_INTEGRATION.md
    └── GOVERNANCE_AND_KPIS.md
```

## Quick Start

### Streamlit app (recommended)

From the project root:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL (e.g. http://localhost:8501). Use the sidebar to switch between **Dashboard**, **Browse lessons**, **Add lesson**, **Validation**, **Duplicates**, and **Reports**.

### CLI

1. **Add lessons** to `data/lessons_master.csv` (or via the Streamlit **Add lesson** page; or sync from SharePoint; see docs).
2. **Validate**:
   ```bash
   python scripts/validate_lessons.py
   ```
3. **View KPIs**:
   ```bash
   python scripts/kpi_summary.py
   ```
4. **Generate all reports** (validation, duplicates, KPI, dashboard CSV):
   ```bash
   python scripts/run_reports.py
   ```

## Lesson Data Model

| Field | Description |
|-------|-------------|
| Lesson ID | Unique identifier |
| Title | One-line action-oriented summary |
| Category | Development, Engineering, Procurement, Construction, O&M |
| Technical Block | Civil, HV & Grid, PV, BESS |
| Sub-category | Detailed technical area or subcontracting package |
| Project Phase | Development, Pre-Execution, Construction, O&M |
| Root Cause | Underlying reason |
| What Happened | Concise factual description |
| Impact | Cost, schedule, quality, safety |
| Lesson Learned | Single-sentence learning |
| Recommendation | Mandatory future action |
| Recommendation Due Date | Optional; target date for implementing the recommendation |
| Keywords | Search tags |
| Status | Draft, Approved (when creating, only Draft is allowed) |
| Implementation Status | Not Implemented, Implemented (tracks whether recommendation was applied) |
| Owner | Responsible role |
| Created Date / Modified Date | Optional metadata |

## Classification Axes (Controlled Values)

- **Category**: Development, Engineering, Procurement, Construction, O&M  
- **Technical Block**: Civil, HV & Grid, PV, BESS  
- **Project Phase**: Development, Pre-Execution, Construction, O&M  
- **Status**: Draft, Approved  
- **Implementation Status**: Not Implemented, Implemented  

Reference CSVs in `data/` define these; Python validation enforces them and prevents free-text drift.

## Lifecycle

**Capture (Draft) → Review → Approval → Implementation Follow Up**

Use **Implementation Follow Up** (after approval) to mark recommendations as **Implemented** when the action has been taken. Set a **Recommendation Due Date** when adding a lesson to track overdue items.

## Governance KPIs

- **Repeated Issues** – same technical block / category / root cause
- **Capture-to-Approval Time** – process efficiency
- **% Recommendations Implemented** – share of approved lessons with recommendation implemented
- **Overdue (not implemented)** – approved lessons past due date still not implemented

See `docs/GOVERNANCE_AND_KPIS.md` for definitions and usage.

## Dependencies

Standard library only (no `pip` install required for core CSV workflow). See `requirements.txt`.

## SharePoint and Power BI

- **SharePoint**: Use `docs/SHAREPOINT_LIST_SCHEMA.md` to create the list and map columns; sync list data to `lessons_master.csv` for Python processing.
- **Power BI**: Connect to `data/lessons_master.csv` or `reports/dashboard_export.csv`; see `docs/POWER_BI_INTEGRATION.md` for suggested visuals and KPIs.
