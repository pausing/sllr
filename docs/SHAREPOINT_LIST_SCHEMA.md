# SharePoint List Schema for SLLR

Map each CSV column to a SharePoint List field. Use column validation and choice columns to enforce controlled vocabularies.

## List: Lessons Learned

| CSV Column      | SharePoint Field Type | Required | Choices / Notes |
|-----------------|------------------------|----------|------------------|
| Lesson ID       | Single line text       | Yes      | Auto-generated or manual; unique |
| Title           | Single line text       | Yes      | One-line action-oriented summary; max length 200 |
| Technical Block | Choice                 | Yes      | Civil, HV & Grid, PV, BESS |
| Project Phase   | Choice                 | Yes      | Development, Pre-Execution, Construction, O&M |
| Event Description | Multiple lines text  | Yes      | Concise factual description of the event |
| Root Cause      | Multiple lines text    | Yes      | Underlying reason |
| Impact          | Choice or text         | Yes      | Cost, Schedule, Quality, Safety (or multi-select) |
| Lesson Learned  | Multiple lines text    | Yes      | Single-sentence learning; max 500 chars recommended |
| Recommendation  | Multiple lines text    | Yes      | Mandatory future action |
| Implementation Owner | Person or email   | No       | Required when approving (Draft → Approved) |
| Implementation Due Date | Date             | No       | Required when approving; target date for implementing the recommendation |
| Keywords        | Multiple lines or tags | No       | Search tags |
| Status          | Choice                 | Yes      | Draft, Approved (new items start as Draft) |
| Implementation Status | Choice            | Yes      | Not Implemented, Implemented (track recommendation implementation) |
| Owner           | Person or single line  | Yes      | Responsible role |
| Created Date    | Date and time          | No       | Auto on create |
| Modified Date   | Date and time          | No       | Auto on edit |

Legacy columns Category, Sub-category, What Happened, and Recommendation Due Date are not required. What Happened maps to Event Description on import; Recommendation Due Date maps to Implementation Due Date when the latter is empty.

## Validation Formulas (examples)

- **Title**: `=LEN(Title)<=200`
- **Status**: Use Choice column with only: Draft, Approved.
- **Lesson ID**: Enforce uniqueness via list settings or workflow.

## Sync with CSV

- Export list to CSV periodically; replace or append into `data/lessons_master.csv`.
- Or use SharePoint REST API / Power Automate to push new items into the CSV repo; then run Python validation and reports.
