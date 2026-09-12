import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, Lesson, References } from '../lib/api'
import { Card, Button, Field, TextInput, TextArea, Select } from '../components/ui'

export function LessonEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [refs, setRefs] = useState<References | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    Promise.all([api.getLesson(id), api.getReferences()])
      .then(([l, r]) => {
        setLesson(l)
        setRefs(r)
      })
      .catch(console.error)
  }, [id])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id || !lesson) return
    
    setLoading(true)
    setError('')
    
    try {
      await api.updateLesson(id, lesson)
      navigate('/lessons')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update lesson')
    } finally {
      setLoading(false)
    }
  }

  if (!lesson || !refs) return <div className="text-muted">Loading...</div>

  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-bold text-text mb-6">Edit Lesson: {lesson['Lesson ID']}</h1>
      
      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-danger/10 border border-danger rounded-md text-danger text-sm">
              {error}
            </div>
          )}

          <Field label="Lesson ID" required>
            <TextInput value={lesson['Lesson ID']} disabled />
            <p className="text-xs text-muted mt-1">Lesson ID cannot be changed</p>
          </Field>

          <Field label="Title" required>
            <TextInput
              value={lesson.Title}
              onChange={(e) => setLesson({ ...lesson, Title: e.target.value })}
              maxLength={200}
              required
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Category" required>
              <Select
                options={refs.categories.map(v => ({ value: v, label: v }))}
                value={lesson.Category}
                onChange={(e) => setLesson({ ...lesson, Category: e.target.value })}
                required
              />
            </Field>

            <Field label="Technical Block" required>
              <Select
                options={refs.technical_blocks.map(v => ({ value: v, label: v }))}
                value={lesson['Technical Block']}
                onChange={(e) => setLesson({ ...lesson, 'Technical Block': e.target.value })}
                required
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Sub-category" required>
              <TextInput
                value={lesson['Sub-category']}
                onChange={(e) => setLesson({ ...lesson, 'Sub-category': e.target.value })}
                required
              />
            </Field>

            <Field label="Project Phase" required>
              <Select
                options={refs.phases.map(v => ({ value: v, label: v }))}
                value={lesson['Project Phase']}
                onChange={(e) => setLesson({ ...lesson, 'Project Phase': e.target.value })}
                required
              />
            </Field>
          </div>

          <Field label="Root Cause" required>
            <TextArea
              value={lesson['Root Cause']}
              onChange={(e) => setLesson({ ...lesson, 'Root Cause': e.target.value })}
              required
            />
          </Field>

          <Field label="What Happened" required>
            <TextArea
              value={lesson['What Happened']}
              onChange={(e) => setLesson({ ...lesson, 'What Happened': e.target.value })}
              required
            />
          </Field>

          <Field label="Impact" required>
            <TextInput
              value={lesson.Impact}
              onChange={(e) => setLesson({ ...lesson, Impact: e.target.value })}
              required
            />
          </Field>

          <Field label="Lesson Learned" required>
            <TextArea
              value={lesson['Lesson Learned']}
              onChange={(e) => setLesson({ ...lesson, 'Lesson Learned': e.target.value })}
              maxLength={500}
              required
            />
          </Field>

          <Field label="Recommendation" required>
            <TextArea
              value={lesson.Recommendation}
              onChange={(e) => setLesson({ ...lesson, Recommendation: e.target.value })}
              required
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Recommendation Due Date">
              <TextInput
                type="date"
                value={lesson['Recommendation Due Date'] || ''}
                onChange={(e) => setLesson({ ...lesson, 'Recommendation Due Date': e.target.value })}
              />
            </Field>

            <Field label="Owner" required>
              <TextInput
                value={lesson.Owner}
                onChange={(e) => setLesson({ ...lesson, Owner: e.target.value })}
                required
              />
            </Field>
          </div>

          <Field label="Keywords">
            <TextInput
              value={lesson.Keywords || ''}
              onChange={(e) => setLesson({ ...lesson, Keywords: e.target.value })}
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Status" required>
              <Select
                options={refs.statuses.map(v => ({ value: v, label: v }))}
                value={lesson.Status}
                onChange={(e) => setLesson({ ...lesson, Status: e.target.value })}
                required
              />
            </Field>

            <Field label="Implementation Status" required>
              <Select
                options={refs.implementation_statuses.map(v => ({ value: v, label: v }))}
                value={lesson['Implementation Status']}
                onChange={(e) => setLesson({ ...lesson, 'Implementation Status': e.target.value })}
                required
              />
            </Field>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
            <Button type="button" variant="ghost" onClick={() => navigate('/lessons')}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
