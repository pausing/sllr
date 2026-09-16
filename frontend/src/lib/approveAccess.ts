import type { Lesson } from './api'

export function visibleLessonsForApprove(
  lessons: Lesson[],
  isAdmin: boolean,
  allowedBlocks: string[],
): Lesson[] {
  if (isAdmin) return lessons
  const allowed = new Set(allowedBlocks)
  return lessons.filter(
    (lesson) => lesson.Status === 'Draft' && allowed.has(lesson['Technical Block']),
  )
}

export function canChangeLessonStatus(
  lesson: Lesson,
  isAdmin: boolean,
  allowedBlocks: string[],
): boolean {
  if (isAdmin) return true
  return lesson.Status === 'Draft' && allowedBlocks.includes(lesson['Technical Block'])
}
