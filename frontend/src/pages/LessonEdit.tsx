import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { LessonForm } from '../components/LessonForm'
import { Button, Card, StatusDot } from '../components/ui'
import { api, Lesson, PortalMe, References } from '../lib/api'
import { canEditLesson } from '../lib/lessonAccess'

function displayValue(value?: string | null): string {
  const text = (value ?? '').trim()
  return text || '—'
}

function DetailField({ label, value, wide }: { label: string; value?: string | null; wide?: boolean }) {
  return (
    <div className={wide ? 'sm:col-span-2' : undefined}>
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 whitespace-pre-wrap break-words text-text">{displayValue(value)}</div>
    </div>
  )
}

export function LessonEdit() {
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [refs, setRefs] = useState<References | null>(null)
  const [me, setMe] = useState<PortalMe | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  let lessonId = id ?? ''
  try {
    lessonId = lessonId ? decodeURIComponent(lessonId) : ''
  } catch {
    /* keep raw id if it is not valid percent-encoding */
  }
  const allowedToEdit = canEditLesson(me, lesson?.Owner)
  const wantEdit = searchParams.get('edit') === '1'
  const editing = allowedToEdit && wantEdit

  useEffect(() => {
    if (!lessonId) return
    Promise.all([api.getLesson(lessonId), api.getReferences(), api.getMe().catch(() => null)])
      .then(([l, r, user]) => {
        setLesson(l)
        setRefs(r)
        setMe(user)
      })
      .catch(console.error)
  }, [lessonId])

  const setEditing = (on: boolean) => {
    const next = new URLSearchParams(searchParams)
    if (on) next.set('edit', '1')
    else next.delete('edit')
    setSearchParams(next, { replace: true })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!lessonId || !lesson || !allowedToEdit) return

    setLoading(true)
    setError('')

    try {
      await api.updateLesson(lessonId, lesson)
      navigate('/lessons')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update lesson')
    } finally {
      setLoading(false)
    }
  }

  if (!lesson || !refs) return <div className="text-muted">Loading...</div>

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4">
        <Link to="/lessons" className="text-sm text-accent hover:underline">
          ← Back to Browse
        </Link>
      </div>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-3">
            <span className="font-mono text-sm text-accent">{lesson['Lesson ID']}</span>
            <StatusDot status={lesson.Status} />
          </div>
          <h1 className="break-words text-2xl font-bold text-text md:text-3xl">
            {editing ? `Edit Lesson` : lesson.Title}
          </h1>
          {editing ? (
            <p className="mt-1 font-mono text-sm text-muted">{lesson['Lesson ID']}</p>
          ) : null}
        </div>
        {allowedToEdit && !editing ? (
          <Button variant="primary" className="shrink-0" onClick={() => setEditing(true)}>
            Edit
          </Button>
        ) : null}
      </div>

      {editing ? (
        <Card>
          <LessonForm
            lesson={lesson}
            refs={refs}
            error={error}
            loading={loading}
            onChange={setLesson}
            onSubmit={handleSubmit}
            onCancel={() => setEditing(false)}
          />
        </Card>
      ) : (
        <div className="space-y-4">
          <Card>
            <h2 className="mb-4 text-lg font-medium text-text">Overview</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Lesson ID" value={lesson['Lesson ID']} />
              <DetailField label="Title" value={lesson.Title} />
              <DetailField label="Status" value={lesson.Status} />
              <DetailField label="Implementation Status" value={lesson['Implementation Status']} />
              <DetailField label="Owner" value={lesson.Owner} />
              <DetailField label="Keywords" value={lesson.Keywords} />
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-medium text-text">Classification</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Category" value={lesson.Category} />
              <DetailField label="Technical Block" value={lesson['Technical Block']} />
              <DetailField label="Sub-category" value={lesson['Sub-category']} />
              <DetailField label="Project Phase" value={lesson['Project Phase']} />
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-medium text-text">What we learned</h2>
            <div className="grid grid-cols-1 gap-4">
              <DetailField label="Root Cause" value={lesson['Root Cause']} wide />
              <DetailField label="What Happened" value={lesson['What Happened']} wide />
              <DetailField label="Impact" value={lesson.Impact} wide />
              <DetailField label="Lesson Learned" value={lesson['Lesson Learned']} wide />
              <DetailField label="Recommendation" value={lesson.Recommendation} wide />
              <DetailField label="Recommendation Due Date" value={lesson['Recommendation Due Date']} />
            </div>
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-medium text-text">Record</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Created Date" value={lesson['Created Date']} />
              <DetailField label="Modified Date" value={lesson['Modified Date']} />
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
