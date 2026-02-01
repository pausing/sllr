# Power BI Integration

Connect Power BI to the SLLR CSV repository or to the SharePoint List for dashboards and trend analysis.

## Data Sources

1. **CSV repository**  
   - Point Power BI to `data/lessons_master.csv` and optionally `reports/dashboard_export.csv` (includes computed columns: Is_Embedded, Reuse_Count_Num, Validation_Errors).
2. **SharePoint List**  
   - Use “SharePoint Online list” connector; select the Lessons Learned list.

## Suggested Visuals and KPIs

| KPI / Visual | Purpose |
|--------------|--------|
| % Lessons Embedded | Gauge or card: measure organizational learning |
| Lessons Reused | Count of lessons with Reuse Count > 0 |
| Repeated Issues | Count of (Discipline × Failure Type × Root Cause) with more than one lesson |
| Capture-to-Approval Time | Average days from Created Date to Modified Date for Status = Approved |
| Discipline heatmap | Lessons by Discipline (and optionally Project Phase) |
| Failure Type trend | Count by Failure Type over time |
| Status funnel | Draft → Approved → Embedded |
| Top Root Causes | Table or bar chart of recurring Root Cause values |

## Dashboard Export CSV

The script `scripts/run_reports.py` generates `reports/dashboard_export.csv` with:

- All lesson columns plus:
  - **Is_Embedded**: 1 if Status = Embedded, else 0
  - **Reuse_Count_Num**: numeric Reuse Count
  - **Validation_Errors**: semicolon-separated validation messages

Use this file in Power BI for calculated metrics and filtering on data quality.

## Refresh

- If using CSV: refresh the dataset after running Python reports or after updating `lessons_master.csv`.
- If using SharePoint: set scheduled refresh or refresh on open.
