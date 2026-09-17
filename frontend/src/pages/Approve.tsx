import { useEffect, useState } from 'react'
import { api, Lesson, MyApproverRules, References, SllrUser } from '../lib/api'
import { canChangeLessonStatus, visibleLessonsForApprove } from '../lib/approveAccess'
import { Button, Card, Field, Select, StatusDot, TextInput } from '../components/ui'

type PendingApprove = {
  id: string
  owner: string
  due: string
}

export function Approve() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [rules, setRules] = useState<MyApproverRules | null>(null)
  const [portalUsers, setPortalUsers] = useState<SllrUser[]>([])
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState<PendingApprove | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.getReferences(),
      api.getLessons(),
      api.getMyApproverRules(),
      api.getPortalSllrUsers(),
    ])
      .then(([r, l, myRules, portal]) => {
        setRefs(r)
        setLessons(l)
        setRules(myRules)
        setPortalUsers(portal.users)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const isAdmin = rules?.admin === true
  const allowedBlocks = rules?.technical_blocks ?? []
  const fallbackBlocks = rules?.fallback_blocks ?? []
  const visibleLessons = visibleLessonsForApprove(lessons, isAdmin, allowedBlocks, fallbackBlocks)
  const draftLessons = visibleLessons.filter((l) => l.Status === 'Draft')

  const ownerOptions = [
    { value: '', label: 'Select implementation owner…' },
    ...portalUsers.map((user) => ({
      value: user.email,
      label: user.name ? `${user.name} (${user.email})` : user.email,
    })),
  ]

  const handleStatusChange = async (lesson: Lesson, newStatus: string) => {
    if (!canChangeLessonStatus(lesson, isAdmin, allowedBlocks, fallbackBlocks)) return
    setError('')
    if (newStatus === 'Approved' && lesson.Status !== 'Approved') {
      setPending({
        id: lesson['Lesson ID'],
        owner: lesson['Implementation Owner'] || '',
        due: lesson['Implementation Due Date'] || '',
      })
      return
    }
    try {
      await api.patchLesson(lesson['Lesson ID'], { Status: newStatus })
      setPending(null)
      setLessons(await api.getLessons())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  const confirmApprove = async (lesson: Lesson) => {
    if (!pending || pending.id !== lesson['Lesson ID']) return
    const owner = pending.owner.trim().toLowerCase()
    const due = pending.due.trim()
    if (!owner || !owner.includes('@') || !due) {
      setError('Implementation Owner (email) and Implementation Due Date are required to approve.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await api.patchLesson(lesson['Lesson ID'], {
        Status: 'Approved',
        'Implementation Owner': owner,
        'Implementation Due Date': due,
      })
      setPending(null)
      setLessons(await api.getLessons())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve lesson')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="text-muted">Loading...</div>
  if (!refs) return <div className="text-danger">Failed to load</div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6 md:text-3xl">Approve / Update Status</h1>

      <p className="text-muted mb-6">
        Move lessons along the lifecycle: <strong>Draft</strong> → <strong>Approved</strong>.
        Approving requires an <strong>Implementation Owner</strong> and{' '}
        <strong>Implementation Due Date</strong>.
        {isAdmin
          ? ' As an admin you can update any lesson.'
          : ' You can approve Draft lessons for the Technical Blocks assigned to you, or General when a block has no specific approver.'}
      </p>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      {draftLessons.length > 0 && (
        <Card className="mb-8">
          <h3 className="text-lg font-medium text-text mb-4">Draft Lessons (Ready to Approve)</h3>
          <div className="space-y-3">
            {draftLessons.map((lesson) => (
              <div
                key={lesson['Lesson ID']}
                className="flex flex-col gap-3 p-3 bg-raised rounded-md sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="font-mono text-sm text-accent mb-1">{lesson['Lesson ID']}</div>
                  <div className="text-text break-words">{lesson.Title}</div>
                  <div className="text-sm text-muted break-words">
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
              const canAct = canChangeLessonStatus(lesson, isAdmin, allowedBlocks, fallbackBlocks)
              const isPending = pending?.id === lesson['Lesson ID']
              const ownerInList = ownerOptions.some((opt) => opt.value === (pending?.owner || ''))
              return (
                <div key={lesson['Lesson ID']} className="flex flex-col gap-3 p-3 bg-raised rounded-md">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex flex-wrap items-center gap-3">
                        <span className="font-mono text-sm text-accent">{lesson['Lesson ID']}</span>
                        <StatusDot status={lesson.Status} />
                      </div>
                      <div className="text-text break-words">{lesson.Title}</div>
                      <div className="text-sm text-muted">{lesson['Technical Block']}</div>
                    </div>
                    {canAct ? (
                      <Select
                        options={refs.statuses.map((v) => ({ value: v, label: v }))}
                        value={isPending ? 'Approved' : lesson.Status}
                        onChange={(e) => handleStatusChange(lesson, e.target.value)}
                        className="w-full sm:w-40"
                      />
                    ) : (
                      <span className="text-sm text-muted">View only</span>
                    )}
                  </div>
                  {isPending ? (
                    <div className="grid grid-cols-1 gap-3 border-t border-line pt-3 md:grid-cols-2">
                      <Field label="Implementation Owner" required>
                        {portalUsers.length > 0 ? (
                          <Select
                            options={
                              pending.owner && !ownerInList
                                ? [...ownerOptions, { value: pending.owner, label: pending.owner }]
                                : ownerOptions
                            }
                            value={pending.owner}
                            onChange={(e) =>
                              setPending((current) =>
                                current ? { ...current, owner: e.target.value } : current,
                              )
                            }
                          />
                        ) : (
                          <TextInput
                            type="email"
                            value={pending.owner}
                            onChange={(e) =>
                              setPending((current) =>
                                current ? { ...current, owner: e.target.value } : current,
                              )
                            }
                            placeholder="user@powerlearn.us"
                          />
                        )}
                      </Field>
                      <Field label="Implementation Due Date" required>
                        <TextInput
                          type="date"
                          value={pending.due}
                          onChange={(e) =>
                            setPending((current) =>
                              current ? { ...current, due: e.target.value } : current,
                            )
                          }
                        />
                      </Field>
                      <div className="flex flex-wrap gap-2 md:col-span-2">
                        <Button
                          type="button"
                          variant="primary"
                          disabled={saving}
                          onClick={() => void confirmApprove(lesson)}
                        >
                          {saving ? 'Approving…' : 'Confirm approval'}
                        </Button>
                        <Button type="button" variant="ghost" onClick={() => setPending(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )
}
