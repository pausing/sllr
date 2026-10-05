/** Parse Content-Disposition so single-lesson PDFs keep their Lesson ID filename. */
export function filenameFromContentDisposition(header: string | null | undefined, fallback: string): string {
  if (!header) return fallback
  const star = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(header)
  if (star?.[1]) {
    const raw = star[1].trim().replace(/^"(.*)"$/, '$1')
    try {
      return decodeURIComponent(raw)
    } catch {
      return raw
    }
  }
  const quoted = /filename="([^"]+)"/i.exec(header)
  if (quoted?.[1]) return quoted[1].trim()
  const plain = /filename=([^;]+)/i.exec(header)
  if (plain?.[1]) return plain[1].trim().replace(/^"(.*)"$/, '$1')
  return fallback
}

export function fallbackPdfName(ids?: string[]): string {
  if (ids?.length === 1 && ids[0]) {
    const safe = ids[0].replace(/[^A-Za-z0-9._-]+/g, '_').replace(/^[._]+|[._]+$/g, '')
    return `${safe || 'lesson'}.pdf`
  }
  return 'lessons_learned.pdf'
}
