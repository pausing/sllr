"""Shared lesson JSON for API tests (current schema, no category)."""


def lesson_body(
    lesson_id: str,
    *,
    technical_block: str = "PV",
    owner: str = "Test Owner",
    **overrides,
) -> dict:
    row = {
        "Lesson ID": lesson_id,
        "Title": f"Lesson {lesson_id}",
        "Technical Block": technical_block,
        "Project Phase": "Construction",
        "Event Description": "Test event description",
        "Root Cause": "Test root cause",
        "Impact": "Test impact",
        "Lesson Learned": "Test lesson learned",
        "Recommendation": "Test recommendation",
        "Owner": owner,
    }
    row.update(overrides)
    return row


APPROVE_ASSIGNMENT = {
    "Implementation Owner": "impl.owner@powerlearn.us",
    "Implementation Due Date": "2027-01-15",
}
