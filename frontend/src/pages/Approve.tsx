import { useEffect, useState } from 'react'
import { api, Lesson, References } from '../lib/api'
import { Card, Select, StatusDot } from '../components/ui'

export function Approve() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getReferences(), api.getLessons()])
      .then(([r, l]) => {
        setRefs(r)
        setLessons(l)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      await api.patchLesson(id, { Status: newStatus })
      const updated = await api.getLessons()
      setLessons(updated)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  const draftLessons = lessons.filter(l => l.Status === 'Draft')

  if (loading) return <div className="text-muted">Loading...</div>
  if (!refs) return <div className="text-danger">Failed to load</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">Approve / Update Status</h1>
      
      <p className="text-muted mb-6">
        Move lessons along the lifecycle: <strong>Draft</strong> → <strong>Approved</strong>.
        Select a lesson and choose the new status.
      </p>

      {draftLessons.length > 0 && (
        <Card className="mb-8">
          <h3 className="text-lg font-medium text-text mb-4">Draft Lessons (Ready to Approve)</h3>
          <div className="space-y-3">
            {draftLessons.map((lesson) => (
              <div key={lesson['Lesson ID']} className="flex items-center justify-between p-3 bg-raised rounded-md">
                <div>
                  <div className="font-mono text-sm text-accent mb-1">{lesson['Lesson ID']}</div>
                  <div className="text-text">{lesson.Title}</div>
                  <div className="text-sm text-muted">Owner: {lesson.Owner}</div>
                </div>
                <StatusDot status={lesson.Status} />
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <h3 className="text-lg font-medium text-text mb-4">All Lessons</h3>
        {lessons.length === 0 ? (
          <p className="text-muted">No lessons yet.</p>
        ) : (
          <div className="space-y-3">
            {lessons.map((lesson) => (
              <div key={lesson['Lesson ID']} className="flex items-center justify-between p-3 bg-raised rounded-md">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-sm text-accent">{lesson['Lesson ID']}</span>
                    <StatusDot status={lesson.Status} />
                  </div>
                  <div className="text-text">{lesson.Title}</div>
                </div>
                <Select
                  options={refs.statuses.map(v => ({ value: v, label: v }))}
                  value={lesson.Status}
                  onChange={(e) => handleStatusChange(lesson['Lesson ID'], e.target.value)}
                  className="w-40"
                />
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
