import { FormEvent, useEffect, useId, useState } from 'react'
import { Button, Card, ConfirmDialog } from './ui'
import {
  api,
  LessonAttachment,
  MAX_ATTACHMENT_BYTES,
  MAX_ATTACHMENT_LABEL,
  PortalMe,
} from '../lib/api'
import { canEditLesson } from '../lib/lessonAccess'
import { formatBytes } from '../lib/formatBytes'

function formatUploadedAt(iso?: string): string {
  const raw = (iso ?? '').trim()
  if (!raw) return '—'
  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return raw
  return parsed.toLocaleString()
}

export function LessonAttachments({
  lessonId,
  owner,
  me,
}: {
  lessonId: string
  owner?: string | null
  me: PortalMe | null
}) {
  const inputId = useId()
  const helpId = useId()
  const errorId = useId()
  const canManage = canEditLesson(me, owner)
  const [items, setItems] = useState<LessonAttachment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [pendingDelete, setPendingDelete] = useState<LessonAttachment | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = async () => {
    setItems(await api.getAttachments(lessonId))
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .getAttachments(lessonId)
      .then((rows) => {
        if (!cancelled) setItems(rows)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load attachments')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [lessonId])

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = event.currentTarget
    const input = form.elements.namedItem('file') as HTMLInputElement | null
    const file = input?.files?.[0]
    setError('')
    if (!file) {
      setError('Choose a file to attach.')
      return
    }
    if (file.size > MAX_ATTACHMENT_BYTES) {
      setError(`File is larger than the ${MAX_ATTACHMENT_LABEL} limit.`)
      return
    }
    setUploading(true)
    try {
      await api.uploadAttachment(lessonId, file)
      form.reset()
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload attachment')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async () => {
    if (!pendingDelete) return
    setDeleting(true)
    setError('')
    try {
      await api.deleteAttachment(lessonId, pendingDelete.id)
      setPendingDelete(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete attachment')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Card>
      <h2 className="mb-1 text-lg font-medium text-text">Attachments</h2>
      <p id={helpId} className="mb-4 text-sm text-muted">
        Maximum size: {MAX_ATTACHMENT_LABEL} per file.
      </p>

      {loading ? <p className="text-sm text-muted">Loading attachments…</p> : null}

      {!loading && items.length === 0 ? (
        <p className="text-sm text-muted">No files attached yet.</p>
      ) : null}

      {items.length > 0 ? (
        <ul className="divide-y divide-line rounded-md border border-line">
          {items.map((item) => (
            <li key={item.id} className="flex flex-col gap-2 px-3 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <div className="break-all font-medium text-text">{item.filename}</div>
                <div className="mt-1 text-xs text-muted">
                  {formatBytes(item.size_bytes)}
                  <span className="mx-2 text-line">·</span>
                  {formatUploadedAt(item.uploaded_at)}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <a
                  href={api.attachmentDownloadUrl(lessonId, item.id)}
                  className="inline-flex min-h-11 items-center rounded-md border border-line bg-raised px-4 py-2 text-sm font-medium text-text hover:bg-[#222936]"
                >
                  Download
                </a>
                {canManage ? (
                  <Button type="button" variant="ghost" className="text-danger" onClick={() => setPendingDelete(item)}>
                    Delete
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {canManage ? (
        <form className="mt-4 space-y-3" onSubmit={(event) => void handleUpload(event)}>
          <div>
            <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-text">
              Attach a file
            </label>
            <input
              id={inputId}
              name="file"
              type="file"
              aria-describedby={`${helpId}${error ? ` ${errorId}` : ''}`}
              aria-invalid={error ? true : undefined}
              className="block w-full min-h-11 cursor-pointer rounded-md border border-line bg-raised px-3 py-2 text-sm text-text file:mr-3 file:min-h-11 file:cursor-pointer file:rounded-md file:border-0 file:bg-accent-dim file:px-3 file:text-accent hover:file:bg-accent/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            />
          </div>
          <Button type="submit" variant="primary" disabled={uploading}>
            {uploading ? 'Uploading…' : 'Upload file'}
          </Button>
        </form>
      ) : null}

      {error ? (
        <p id={errorId} className="mt-3 text-sm text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <ConfirmDialog
        open={pendingDelete != null}
        title="Delete this attachment?"
        busy={deleting}
        confirmLabel="Delete"
        onConfirm={() => void handleDelete()}
        onCancel={() => {
          if (!deleting) setPendingDelete(null)
        }}
      >
        <p>
          Permanently delete{' '}
          <span className="break-all text-text">{pendingDelete?.filename}</span>
          {pendingDelete ? ` (${formatBytes(pendingDelete.size_bytes)})` : null}.
        </p>
      </ConfirmDialog>
    </Card>
  )
}
