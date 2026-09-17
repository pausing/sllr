import type { Lesson } from './api'

const GENERAL = 'General'

export function visibleLessonsForApprove(
  lessons: Lesson[],
  isAdmin: boolean,
  allowedBlocks: string[],
  fallbackBlocks: string[] = [],
): Lesson[] {
  if (isAdmin) return lessons
  const allowed = new Set(allowedBlocks)
  const fallback = new Set(fallbackBlocks)
  const hasGeneral = allowed.has(GENERAL)
  return lessons.filter((lesson) => {
    if (lesson.Status !== 'Draft') return false
    const block = lesson['Technical Block']
    if (allowed.has(block) && block !== GENERAL) return true
    return hasGeneral && fallback.has(block)
  })
}

export function canChangeLessonStatus(
  lesson: Lesson,
  isAdmin: boolean,
  allowedBlocks: string[],
  fallbackBlocks: string[] = [],
): boolean {
  if (isAdmin) return true
  if (lesson.Status !== 'Draft') return false
  const allowed = new Set(allowedBlocks)
  const block = lesson['Technical Block']
  if (allowed.has(block) && block !== GENERAL) return true
  return allowed.has(GENERAL) && fallbackBlocks.includes(block)
}
