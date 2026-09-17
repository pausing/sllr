import type { Lesson } from './api'

export function lessonMatchesQuery(lesson: Lesson, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return Object.values(lesson).some((value) => String(value ?? '').toLowerCase().includes(needle))
}
