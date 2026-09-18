import type { Lesson, PortalMe } from './api'

export function normalizeEmail(email?: string | null): string {
  return (email ?? '').trim().toLowerCase()
}

export function emailsMatch(left?: string | null, right?: string | null): boolean {
  const a = normalizeEmail(left)
  const b = normalizeEmail(right)
  return Boolean(a) && a === b
}

/** Portal admin or lesson Owner (case-insensitive, trimmed). */
export function canEditLesson(
  me: Pick<PortalMe, 'admin' | 'email'> | null | undefined,
  owner?: string | null,
): boolean {
  if (me?.admin === true) return true
  return emailsMatch(me?.email, owner)
}

export function lessonPath(id: string, edit = false): string {
  const path = `/lessons/${encodeURIComponent(id)}`
  return edit ? `${path}?edit=1` : path
}

/** Portal admin any lesson; owner only while Draft (not Approved / implemented). */
export function canDeleteLesson(
  me: Pick<PortalMe, 'admin' | 'email'> | null | undefined,
  lesson?: Pick<Lesson, 'Owner' | 'Status' | 'Implementation Status'> | null,
): boolean {
  if (!lesson) return false
  if (me?.admin === true) return true
  if (!emailsMatch(me?.email, lesson.Owner)) return false
  const status = (lesson.Status ?? '').trim()
  const impl = (lesson['Implementation Status'] ?? '').trim()
  return status === 'Draft' && impl !== 'Implemented'
}
