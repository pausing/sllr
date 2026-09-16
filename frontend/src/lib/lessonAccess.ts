import type { PortalMe } from './api'

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
