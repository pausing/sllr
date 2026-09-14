"""
Lessons API router - CRUD operations for lessons.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.app.storage import (
    find_lesson_by_id,
    insert_lesson,
    lesson_id_exists,
    load_lessons_with_lock,
    suggest_next_id,
    update_lesson_row,
)
from backend.app.identity import resolve_owner
from src.sllr.loaders import load_all_references
from src.sllr.validation import validate_lesson


router = APIRouter()


class LessonCreate(BaseModel):
    """Lesson creation schema."""
    lesson_id: str = Field(..., alias="Lesson ID")
    title: str = Field(..., max_length=200, alias="Title")
    category: str = Field(..., alias="Category")
    technical_block: str = Field(..., alias="Technical Block")
    sub_category: str = Field(..., alias="Sub-category")
    project_phase: str = Field(..., alias="Project Phase")
    root_cause: str = Field(..., alias="Root Cause")
    what_happened: str = Field(..., alias="What Happened")
    impact: str = Field(..., alias="Impact")
    lesson_learned: str = Field(..., max_length=500, alias="Lesson Learned")
    recommendation: str = Field(..., alias="Recommendation")
    recommendation_due_date: Optional[str] = Field(None, alias="Recommendation Due Date")
    keywords: Optional[str] = Field("", alias="Keywords")
    owner: Optional[str] = Field(None, alias="Owner")

    class Config:
        populate_by_name = True


class LessonUpdate(BaseModel):
    """Lesson update schema (all fields except Lesson ID)."""
    title: Optional[str] = Field(None, max_length=200, alias="Title")
    category: Optional[str] = Field(None, alias="Category")
    technical_block: Optional[str] = Field(None, alias="Technical Block")
    sub_category: Optional[str] = Field(None, alias="Sub-category")
    project_phase: Optional[str] = Field(None, alias="Project Phase")
    root_cause: Optional[str] = Field(None, alias="Root Cause")
    what_happened: Optional[str] = Field(None, alias="What Happened")
    impact: Optional[str] = Field(None, alias="Impact")
    lesson_learned: Optional[str] = Field(None, max_length=500, alias="Lesson Learned")
    recommendation: Optional[str] = Field(None, alias="Recommendation")
    recommendation_due_date: Optional[str] = Field(None, alias="Recommendation Due Date")
    keywords: Optional[str] = Field(None, alias="Keywords")
    status: Optional[str] = Field(None, alias="Status")
    implementation_status: Optional[str] = Field(None, alias="Implementation Status")
    owner: Optional[str] = Field(None, alias="Owner")

    class Config:
        populate_by_name = True


class LessonPatch(BaseModel):
    """Lesson patch schema (partial updates)."""
    status: Optional[str] = Field(None, alias="Status")
    implementation_status: Optional[str] = Field(None, alias="Implementation Status")
    title: Optional[str] = Field(None, alias="Title")
    category: Optional[str] = Field(None, alias="Category")
    technical_block: Optional[str] = Field(None, alias="Technical Block")
    sub_category: Optional[str] = Field(None, alias="Sub-category")
    project_phase: Optional[str] = Field(None, alias="Project Phase")
    root_cause: Optional[str] = Field(None, alias="Root Cause")
    what_happened: Optional[str] = Field(None, alias="What Happened")
    impact: Optional[str] = Field(None, alias="Impact")
    lesson_learned: Optional[str] = Field(None, alias="Lesson Learned")
    recommendation: Optional[str] = Field(None, alias="Recommendation")
    recommendation_due_date: Optional[str] = Field(None, alias="Recommendation Due Date")
    keywords: Optional[str] = Field(None, alias="Keywords")
    owner: Optional[str] = Field(None, alias="Owner")

    class Config:
        populate_by_name = True


@router.get("/lessons")
async def list_lessons(
    technical_block: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    implementation_status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    """
    List all lessons with optional filters.
    """
    lessons = load_lessons_with_lock()
    
    # Apply filters
    if technical_block:
        lessons = [l for l in lessons if l.get("Technical Block") == technical_block]
    if phase:
        lessons = [l for l in lessons if l.get("Project Phase") == phase]
    if status:
        lessons = [l for l in lessons if l.get("Status") == status]
    if implementation_status:
        lessons = [l for l in lessons if l.get("Implementation Status") == implementation_status]
    if category:
        lessons = [l for l in lessons if l.get("Category") == category]
    
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
    """
    # Check for duplicate ID
    if lesson_id_exists(lesson.lesson_id):
        raise HTTPException(status_code=409, detail=f"Lesson ID {lesson.lesson_id} already exists")
    
    # Build the row
    now = datetime.now().strftime("%Y-%m-%d")
    row = {
        "Lesson ID": lesson.lesson_id,
        "Title": lesson.title,
        "Category": lesson.category,
        "Technical Block": lesson.technical_block,
        "Sub-category": lesson.sub_category,
        "Project Phase": lesson.project_phase,
        "Root Cause": lesson.root_cause,
        "What Happened": lesson.what_happened,
        "Impact": lesson.impact,
        "Lesson Learned": lesson.lesson_learned,
        "Recommendation": lesson.recommendation,
        "Recommendation Due Date": lesson.recommendation_due_date or "",
        "Keywords": lesson.keywords or "",
        "Status": "Draft",
        "Implementation Status": "Not Implemented",
        "Owner": resolve_owner(lesson.owner, request),
        "Created Date": now,
        "Modified Date": now,
    }
    
    # Validate
    refs = load_all_references()
    errors = validate_lesson(row, refs)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    
    insert_lesson(row)
    return row


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: str, lesson: LessonUpdate, request: Request):
    """
    Update a lesson (full update except Lesson ID).
    """
    existing = find_lesson_by_id(lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")
    
    # Build updated row
    now = datetime.now().strftime("%Y-%m-%d")
    updated = dict(existing)
    
    # Update provided fields
    if lesson.title is not None:
        updated["Title"] = lesson.title
    if lesson.category is not None:
        updated["Category"] = lesson.category
    if lesson.technical_block is not None:
        updated["Technical Block"] = lesson.technical_block
    if lesson.sub_category is not None:
        updated["Sub-category"] = lesson.sub_category
    if lesson.project_phase is not None:
        updated["Project Phase"] = lesson.project_phase
    if lesson.root_cause is not None:
        updated["Root Cause"] = lesson.root_cause
    if lesson.what_happened is not None:
        updated["What Happened"] = lesson.what_happened
    if lesson.impact is not None:
        updated["Impact"] = lesson.impact
    if lesson.lesson_learned is not None:
        updated["Lesson Learned"] = lesson.lesson_learned
    if lesson.recommendation is not None:
        updated["Recommendation"] = lesson.recommendation
    if lesson.recommendation_due_date is not None:
        updated["Recommendation Due Date"] = lesson.recommendation_due_date
    if lesson.keywords is not None:
        updated["Keywords"] = lesson.keywords
    if lesson.status is not None:
        updated["Status"] = lesson.status
    if lesson.implementation_status is not None:
        updated["Implementation Status"] = lesson.implementation_status
    updated["Owner"] = resolve_owner(lesson.owner, request, existing.get("Owner"))
    
    updated["Modified Date"] = now
    
    # Validate
    refs = load_all_references()
    errors = validate_lesson(updated, refs)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    
    update_lesson_row(lesson_id, updated)
    return updated


@router.patch("/lessons/{lesson_id}")
async def patch_lesson(lesson_id: str, patch: LessonPatch, request: Request):
    """
    Patch a lesson (partial update). Commonly used for status/implementation_status changes.
    """
    existing = find_lesson_by_id(lesson_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")
    
    # Build patched row
    now = datetime.now().strftime("%Y-%m-%d")
    patched = dict(existing)
    
    # Apply patches
    if patch.status is not None:
        patched["Status"] = patch.status
    if patch.implementation_status is not None:
        patched["Implementation Status"] = patch.implementation_status
    if patch.title is not None:
        patched["Title"] = patch.title
    if patch.category is not None:
        patched["Category"] = patch.category
    if patch.technical_block is not None:
        patched["Technical Block"] = patch.technical_block
    if patch.sub_category is not None:
        patched["Sub-category"] = patch.sub_category
    if patch.project_phase is not None:
        patched["Project Phase"] = patch.project_phase
    if patch.root_cause is not None:
        patched["Root Cause"] = patch.root_cause
    if patch.what_happened is not None:
        patched["What Happened"] = patch.what_happened
    if patch.impact is not None:
        patched["Impact"] = patch.impact
    if patch.lesson_learned is not None:
        patched["Lesson Learned"] = patch.lesson_learned
    if patch.recommendation is not None:
        patched["Recommendation"] = patch.recommendation
    if patch.recommendation_due_date is not None:
        patched["Recommendation Due Date"] = patch.recommendation_due_date
    if patch.keywords is not None:
        patched["Keywords"] = patch.keywords
    patched["Owner"] = resolve_owner(patch.owner, request, existing.get("Owner"))
    
    patched["Modified Date"] = now
    
    # Validate
    refs = load_all_references()
    errors = validate_lesson(patched, refs)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    
    update_lesson_row(lesson_id, patched)
    return patched
