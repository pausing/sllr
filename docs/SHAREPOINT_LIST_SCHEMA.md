# SharePoint List Schema for SLLR

Map each CSV column to a SharePoint List field. Use column validation and choice columns to enforce controlled vocabularies.

## List: Lessons Learned

| CSV Column      | SharePoint Field Type | Required | Choices / Notes |
|-----------------|------------------------|----------|------------------|
| Lesson ID       | Single line text       | Yes      | Auto-generated or manual; unique |
| Title           | Single line text       | Yes      | Max length 200 |
| Category        | Choice                 | Yes      | Engineering, Procurement, Construction, O&M |
| Sub-category    | Single line text       | Yes      | Free text (detailed technical area) |
| Discipline      | Choice                 | Yes      | Civil, Electrical, SCADA, Grid, BESS, HSE, Contracts |
| Project Phase   | Choice                 | Yes      | Development, Engineering, Procurement, Construction, Commissioning, O&M |
| Failure Type    | Choice                 | Yes      | Technical, Interface, Vendor, Regulatory, Organizational |
| Root Cause      | Multiple lines text    | Yes      | Plain text |
| What Happened   | Multiple lines text    | Yes      | Concise factual description |
| Impact          | Choice or text         | Yes      | Cost, Schedule, Quality, Safety (or multi-select) |
| Lesson Learned  | Multiple lines text    | Yes      | Single-sentence learning; max 500 chars recommended |
| Recommendation  | Multiple lines text    | Yes      | Mandatory future action |
| Applicability   | Multiple lines text    | No       | Technology, geography, project type |
| Keywords        | Multiple lines or tags | No       | Search tags |
| Status          | Choice                 | Yes      | Draft, Approved, Embedded |
| Owner           | Person or single line  | Yes      | Responsible role |
| Created Date    | Date and time          | No       | Auto on create |
| Modified Date   | Date and time          | No       | Auto on edit |
| Reuse Count     | Number                 | No       | Integer; default 0 |

## Validation Formulas (examples)

- **Title**: `=LEN(Title)<=200`
- **Status**: Use Choice column with only: Draft, Approved, Embedded.
- **Lesson ID**: Enforce uniqueness via list settings or workflow.

## Sync with CSV

- Export list to CSV periodically; replace or append into `data/lessons_master.csv`.
- Or use SharePoint REST API / Power Automate to push new items into the CSV repo; then run Python validation and reports.
