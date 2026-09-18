import { useState } from 'react'
import { useNavigate } from 'react-router'
import { api, Lesson } from '../lib/api'
import { Button, ConfirmDialog } from './ui'

export function deletedLessonNotice(lesson: Pick<Lesson, 'Lesson ID' | 'Title'>): string {
  return `Deleted ${lesson['Lesson ID']} “${lesson.Title}”.`
}

export function DeleteLessonButton({
  lesson,
  onDeleted,
}: {
  lesson: Lesson
  onDeleted?: (lesson: Lesson) => void
}) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const id = lesson['Lesson ID']
  const title = lesson.Title

  const handleConfirm = async () => {
    setBusy(true)
    setError('')
    try {
      await api.deleteLesson(id)
      setOpen(false)
      if (onDeleted) {
        onDeleted(lesson)
        return
      }
      navigate('/lessons', { state: { notice: deletedLessonNotice(lesson) } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete lesson')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button type="button" variant="danger" onClick={() => setOpen(true)}>
        Delete
      </Button>
      <ConfirmDialog
        open={open}
        title="Delete this lesson?"
        busy={busy}
        error={error}
        confirmLabel="Delete"
        onConfirm={() => void handleConfirm()}
        onCancel={() => {
          if (!busy) {
            setOpen(false)
            setError('')
          }
        }}
      >
        <p>
          Permanently delete <span className="font-mono text-accent">{id}</span>
          {title ? (
            <>
              {' '}
              — <span className="text-text">{title}</span>
            </>
          ) : null}
          .
        </p>
        <p className="mt-2 font-medium text-danger">This cannot be undone.</p>
      </ConfirmDialog>
    </>
  )
}
