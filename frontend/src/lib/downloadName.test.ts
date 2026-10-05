import { fallbackPdfName, filenameFromContentDisposition } from './downloadName'

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message)
}

export function runDownloadNameChecks(): void {
  assert(fallbackPdfName() === 'lessons_learned.pdf', 'all lessons fallback')
  assert(fallbackPdfName(['LL-12']) === 'LL-12.pdf', 'single id fallback')
  assert(fallbackPdfName(['LL/1']) === 'LL_1.pdf', 'sanitize slash')
  assert(
    filenameFromContentDisposition('attachment; filename="LL-9.pdf"', 'x.pdf') === 'LL-9.pdf',
    'quoted filename',
  )
  assert(
    filenameFromContentDisposition("attachment; filename=\"x.pdf\"; filename*=UTF-8''LL-9.pdf", 'x.pdf') ===
      'LL-9.pdf',
    'filename* wins',
  )
  assert(filenameFromContentDisposition(null, 'lessons_learned.pdf') === 'lessons_learned.pdf', 'missing header')
}

runDownloadNameChecks()
