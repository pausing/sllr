"""
Lessons API router - CRUD operations for lessons.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.app.activity import changed_values, lesson_write_action, log_activity
from backend.app.approval import enforce_approval_if_needed, enforce_implementation_on_approve
from backend.app.storage import (
    delete_lesson_row,
    find_lesson_by_id,
    insert_lesson,
    lesson_id_exists,
    load_lessons_with_lock,
    suggest_next_id,
    update_lesson_row,
)
from backend.app.identity import require_lesson_deleter, require_lesson_editor, resolve_owner
from src.sllr.loaders import load_all_references
from src.sllr.validation import validate_lesson


router = APIRouter()


class LessonCreate(BaseModel):
    """Lesson creation schema. Recommendation due date is not accepted on create."""
    lesson_id: str = Field(..., alias="Lesson ID")
    title: str = Field(..., max_length=200, alias="Title")
    technical_block: str = Field(..., alias="Technical Block")
    project_phase: str = Field(..., alias="Project Phase")
    event_description: str = Field(..., alias="Event Description")
    root_cause: str = Field(..., alias="Root Cause")
    impact: str = Field(..., alias="Impact")
    lesson_learned: str = Field(..., max_length=500, alias="Lesson Learned")
    recommendation: str = Field(..., alias="Recommendation")
    keywords: Optional[str] = Field("", alias="Keywords")
    owner: Optional[str] = Field(None, alias="Owner")

    class Config:
        populate_by_name = True
        extra = "ignore"


class LessonUpdate(BaseModel):
    """Lesson update schema (all fields except Lesson ID)."""
    title: Optional[str] = Field(None, max_length=200, alias="Title")
    technical_block: Optional[str] = Field(None, alias="Technical Block")
    project_phase: Optional[str] = Field(None, alias="Project Phase")
    event_description: Optional[str] = Field(None, alias="Event Description")
    root_cause: Optional[str] = Field(None, alias="Root Cause")
    impact: Optional[str] = Field(None, alias="Impact")
    lesson_learned: Optional[str] = Field(None, max_length=500, alias="Lesson Learned")
    recommendation: Optional[str] = Field(None, alias="Recommendation")
    implementation_owner: Optional[str] = Field(None, alias="Implementation Owner")
    implementation_due_date: Optional[str] = Field(None, alias="Implementation Due Date")
    keywords: Optional[str] = Field(None, alias="Keywords")
    status: Optional[str] = Field(None, alias="Status")
    implementation_status: Optional[str] = Field(None, alias="Implementation Status")
    owner: Optional[str] = Field(None, alias="Owner")

    class Config:
        populate_by_name = True
        extra = "ignore"


class LessonPatch(BaseModel):
    """Lesson patch schema (partial updates)."""
    status: Optional[str] = Field(None, alias="Status")
    implementation_status: Optional[str] = Field(None, alias="Implementation Status")
    title: Optional[str] = Field(None, alias="Title")
    technical_block: Optional[str] = Field(None, alias="Technical Block")
    project_phase: Optional[str] = Field(None, alias="Project Phase")
    event_description: Optional[str] = Field(None, alias="Event Description")
    root_cause: Optional[str] = Field(None, alias="Root Cause")
    impact: Optional[str] = Field(None, alias="Impact")
    lesson_learned: Optional[str] = Field(None, alias="Lesson Learned")
    recommendation: Optional[str] = Field(None, alias="Recommendation")
    implementation_owner: Optional[str] = Field(None, alias="Implementation Owner")
    implementation_due_date: Optional[str] = Field(None, alias="Implementation Due Date")
    keywords: Optional[str] = Field(None, alias="Keywords")
    owner: Optional[str] = Field(None, alias="Owner")

    class Config:
        populate_by_name = True
        extra = "ignore"


_STATUS_PATCH_FIELDS = frozenset(
    {
        "status",
        "implementation_status",
        "implementation_owner",
        "implementation_due_date",
    }
)


def _patch_changes_content(patch: LessonPatch) -> bool:
    """True when the patch includes fields other than status / implementation assignment."""
    payload = patch.model_dump(exclude_unset=True)
    return bool(set(payload) - _STATUS_PATCH_FIELDS)


def _lesson_matches_query(lesson: dict[str, Any], q: str) -> bool:
    needle = (q or "").strip().lower()
    if not needle:
        return True
    return any(needle in str(value or "").lower() for value in lesson.values())


def _apply_update_fields(target: dict[str, Any], payload: Dict[str, Any]) -> None:
    mapping = {
        "title": "Title",
        "technical_block": "Technical Block",
        "project_phase": "Project Phase",
        "event_description": "Event Description",
        "root_cause": "Root Cause",
        "impact": "Impact",
        "lesson_learned": "Lesson Learned",
        "recommendation": "Recommendation",
        "implementation_owner": "Implementation Owner",
        "implementation_due_date": "Implementation Due Date",
        "keywords": "Keywords",
        "status": "Status",
        "implementation_status": "Implementation Status",
    }
    for key, column in mapping.items():
        if key in payload and payload[key] is not None:
            target[column] = payload[key]


@router.get("/lessons")
async def list_lessons(
    technical_block: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    implementation_status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    """
    List all lessons with optional filters. ``q`` matches any lesson field.
    """
    lessons = load_lessons_with_lock()

    if technical_block:
        lessons = [l for l in lessons if l.get("Technical Block") == technical_block]
    if phase:
        lessons = [l for l in lessons if l.get("Project Phase") == phase]
    if status:
        lessons = [l for l in lessons if l.get("Status") == status]
    if implementation_status:
        lessons = [l for l in lessons if l.get("Implementation Status") == implementation_status]
    if q:
        lessons = [l for l in lessons if _lesson_matches_query(l, q)]

    return lessons


@router.get("/lessons/next-id")
async def get_next_id():
    """
    Suggest the next available lesson ID.
    """
    return {"suggested_id": suggest_next_id()}


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str):
    """
    Get a single lesson by ID.
    """
    lesson = find_lesson_by_id(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")
    return lesson


@router.post("/lessons", status_code=201)
async def create_lesson(lesson: LessonCreate, request: Request):
    """
    Create a new lesson. Status is forced to Draft, Implementation Status to Not Implemented.
    Returns 409 if lesson ID already exists, 422 if validation fails.
    Owner defaults to X-Powerlearn-Email when the client omits it.
    Implementation Owner / Due Date are assigned later on approval.
    """
    if lesson_id_exists(lesson.lesson_id):
        raise HTTPException(status_code=409, detail=f"Lesson ID {lesson.lesson_id} already exists")

    now = datetime.now().strftime("%Y-%m-%d")
    row = {
        "Lesson ID": lesson.lesson_id,
        "Title": lesson.title,
        "Technical Block": lesson.technical_block,
        "Project Phase": lesson.project_phase,
        "Event Description": lesson.event_description,
        "Root Cause": lesson.root_cause,
        "Impact": lesson.impact,
        "Lesson Learned": lesson.lesson_learned,
        "Recommendation": lesson.recommendation,
        "Implementation Owner": "",
        "Implementation Due Date": "",
        "Keywords": lesson.keywords or "",
        "Status": "Draft",
        "Implementation Status": "Not Implemented",
        "Owner": resolve_owner(lesson.owner, request),
        "Created Date": now,
        "Modified Date": now,
    }

    refs = load_all_references()
    errors = validate_lesson(row, refs)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    insert_lesson(row)
    log_activity(
        request,
        "create_lesson",
        entity_type="lesson",
        entity_id=row["Lesson ID"],
        values={"after": row},
    )
    return row


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: str, lesson: LessonUpdate, request: Request):
    """
    Update a lesson (full update except Lesson ID).
    """
    existing = find_lesson_by_id(lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    require_lesson_editor(request, existing.get("Owner"))

    now = datetime.now().strftime("%Y-%m-%d")
    updated = dict(existing)
    _apply_update_fields(updated, lesson.model_dump(exclude_unset=True))
    updated["Owner"] = resolve_owner(lesson.owner, request, existing.get("Owner"))
    updated["Modified Date"] = now

    refs = load_all_references()
    errors = validate_lesson(updated, refs)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    enforce_approval_if_needed(request, existing, updated)
    enforce_implementation_on_approve(existing, updated)
    update_lesson_row(lesson_id, updated)
    action = lesson_write_action("update_lesson", existing, updated)
    log_activity(
        request,
        action,
        entity_type="lesson",
        entity_id=lesson_id,
        values={"before": existing, "after": updated, "changed": changed_values(existing, updated)},
    )
    return updated


@router.patch("/lessons/{lesson_id}")
async def patch_lesson(lesson_id: str, patch: LessonPatch, request: Request):
    """
    Patch a lesson (partial update). Commonly used for status/implementation_status changes.
    """
    existing = find_lesson_by_id(lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    if _patch_changes_content(patch):
        require_lesson_editor(request, existing.get("Owner"))

    now = datetime.now().strftime("%Y-%m-%d")
    patched = dict(existing)
    _apply_update_fields(patched, patch.model_dump(exclude_unset=True))
    patched["Owner"] = resolve_owner(patch.owner, request, existing.get("Owner"))
    patched["Modified Date"] = now

    refs = load_all_references()
    errors = validate_lesson(patched, refs)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    enforce_approval_if_needed(request, existing, patched)
    enforce_implementation_on_approve(existing, patched)
    update_lesson_row(lesson_id, patched)
    action = lesson_write_action("patch_lesson", existing, patched)
    log_activity(
        request,
        action,
        entity_type="lesson",
        entity_id=lesson_id,
        values={"before": existing, "after": patched, "changed": changed_values(existing, patched)},
    )
    return patched


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: str, request: Request):
    """
    Permanently delete a lesson from SQLite.
    Portal admin: any lesson. Owner: own lesson while still Draft.
    """
    existing = find_lesson_by_id(lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    require_lesson_deleter(request, existing)

    removed = delete_lesson_row(lesson_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    log_activity(
        request,
        "delete_lesson",
        entity_type="lesson",
        entity_id=lesson_id,
        values={
            "before": existing,
            "lesson_id": existing.get("Lesson ID"),
            "title": existing.get("Title"),
        },
    )
    return existing
