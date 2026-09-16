import { useEffect, useState } from 'react'
import { api, Lesson, MyApproverRules, References } from '../lib/api'
import { canChangeLessonStatus, visibleLessonsForApprove } from '../lib/approveAccess'
import { Card, Select, StatusDot } from '../components/ui'

export function Approve() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [rules, setRules] = useState<MyApproverRules | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getReferences(), api.getLessons(), api.getMyApproverRules()])
      .then(([r, l, myRules]) => {
        setRefs(r)
        setLessons(l)
        setRules(myRules)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const isAdmin = rules?.admin === true
  const allowedBlocks = rules?.technical_blocks ?? []
  const visibleLessons = visibleLessonsForApprove(lessons, isAdmin, allowedBlocks)
  const draftLessons = visibleLessons.filter((l) => l.Status === 'Draft')

  const handleStatusChange = async (lesson: Lesson, newStatus: string) => {
    if (!canChangeLessonStatus(lesson, isAdmin, allowedBlocks)) return
    try {
      await api.patchLesson(lesson['Lesson ID'], { Status: newStatus })
      const updated = await api.getLessons()
      setLessons(updated)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  if (loading) return <div className="text-muted">Loading...</div>
  if (!refs) return <div className="text-danger">Failed to load</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">Approve / Update Status</h1>
      
      <p className="text-muted mb-6">
        Move lessons along the lifecycle: <strong>Draft</strong> → <strong>Approved</strong>.
        {isAdmin
          ? ' As an admin you can update any lesson.'
          : ' You can approve Draft lessons for the Technical Blocks assigned to you.'}
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
                  <div className="text-sm text-muted">
                    {lesson['Technical Block']} · Owner: {lesson.Owner}
                  </div>
                </div>
                <StatusDot status={lesson.Status} />
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <h3 className="text-lg font-medium text-text mb-4">
          {isAdmin ? 'All Lessons' : 'Your Draft Lessons'}
        </h3>
        {visibleLessons.length === 0 ? (
          <p className="text-muted">
            {isAdmin
              ? 'No lessons yet.'
              : 'No Draft lessons in your assigned Technical Blocks.'}
          </p>
        ) : (
          <div className="space-y-3">
            {visibleLessons.map((lesson) => {
              const canAct = canChangeLessonStatus(lesson, isAdmin, allowedBlocks)
              return (
                <div key={lesson['Lesson ID']} className="flex items-center justify-between p-3 bg-raised rounded-md">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-mono text-sm text-accent">{lesson['Lesson ID']}</span>
                      <StatusDot status={lesson.Status} />
                    </div>
                    <div className="text-text">{lesson.Title}</div>
                    <div className="text-sm text-muted">{lesson['Technical Block']}</div>
                  </div>
                  {canAct ? (
                    <Select
                      options={refs.statuses.map(v => ({ value: v, label: v }))}
                      value={lesson.Status}
                      onChange={(e) => handleStatusChange(lesson, e.target.value)}
                      className="w-40"
                    />
                  ) : (
                    <span className="text-sm text-muted">View only</span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )
}
