import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { api, References } from '../lib/api'
import { Card, Button, Field, TextInput, TextArea, Select } from '../components/ui'
import {
  NEW_LESSON_INSTRUCTIONS_PARAGRAPHS,
  NEW_LESSON_INSTRUCTIONS_TITLE,
} from '../content/newLessonInstructions'

export function LessonNew() {
  const navigate = useNavigate()
  const [refs, setRefs] = useState<References | null>(null)
  const [nextId, setNextId] = useState('')
  const [formData, setFormData] = useState({
    'Lesson ID': '',
    Title: '',
    'Technical Block': '',
    'Project Phase': '',
    'Event Description': '',
    'Root Cause': '',
    Impact: '',
    'Lesson Learned': '',
    Recommendation: '',
    Keywords: '',
    Owner: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.getReferences(), api.getNextId(), api.getMe().catch(() => null)])
      .then(([r, n, me]) => {
        setRefs(r)
        setNextId(n.suggested_id)
        setFormData((f) => ({
          ...f,
          'Lesson ID': n.suggested_id,
          Owner: f.Owner || me?.email || '',
        }))
      })
      .catch(console.error)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await api.createLesson(formData)
      navigate('/lessons')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create lesson')
    } finally {
      setLoading(false)
    }
  }

  if (!refs) return <div className="text-muted">Loading...</div>

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-text mb-6 md:text-3xl">Add New Lesson</h1>

      <Card className="mb-6">
        <h2 className="mb-3 text-lg font-medium text-text">{NEW_LESSON_INSTRUCTIONS_TITLE}</h2>
        <div className="space-y-3 text-sm leading-relaxed text-muted">
          {NEW_LESSON_INSTRUCTIONS_PARAGRAPHS.map((paragraph) => (
            <p key={paragraph.slice(0, 40)}>{paragraph}</p>
          ))}
        </div>
      </Card>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-danger/10 border border-danger rounded-md text-danger text-sm">
              {error}
            </div>
          )}

          <Field label="Lesson ID" required>
            <TextInput
              value={formData['Lesson ID']}
              onChange={(e) => setFormData({ ...formData, 'Lesson ID': e.target.value })}
              placeholder={nextId}
              required
            />
          </Field>

          <Field label="Title (one-line action-oriented summary)" required>
            <TextInput
              value={formData.Title}
              onChange={(e) => setFormData({ ...formData, Title: e.target.value })}
              maxLength={200}
              required
            />
          </Field>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field
              label="Technical Block"
              required
              hint="The engineering area where the solution is identified and owned. Choose based on where the fix belongs, not necessarily where the problem was observed."
            >
              <Select
                options={[
                  { value: '', label: 'Select...' },
                  ...refs.technical_blocks.map((v) => ({ value: v, label: v })),
                ]}
                value={formData['Technical Block']}
                onChange={(e) => setFormData({ ...formData, 'Technical Block': e.target.value })}
                required
              />
            </Field>

            <Field
              label="Project Phase"
              required
              hint="The point in the project life cycle where the solution must be implemented to prevent recurrence. A lesson found late (e.g. at commissioning) is often solved earlier (e.g. in design or procurement) — pick the phase where the action lands."
            >
              <Select
                options={[
                  { value: '', label: 'Select...' },
                  ...refs.phases.map((v) => ({ value: v, label: v })),
                ]}
                value={formData['Project Phase']}
                onChange={(e) => setFormData({ ...formData, 'Project Phase': e.target.value })}
                required
              />
            </Field>
          </div>

          <Field label="Event Description" required>
            <TextArea
              value={formData['Event Description']}
              onChange={(e) => setFormData({ ...formData, 'Event Description': e.target.value })}
              required
            />
          </Field>

          <Field label="Root Cause" required>
            <TextArea
              value={formData['Root Cause']}
              onChange={(e) => setFormData({ ...formData, 'Root Cause': e.target.value })}
              required
            />
          </Field>

          <Field label="Impact" required>
            <TextInput
              value={formData.Impact}
              onChange={(e) => setFormData({ ...formData, Impact: e.target.value })}
              placeholder="e.g., Cost; Schedule; Quality; Safety"
              required
            />
          </Field>

          <Field label="Lesson Learned (single sentence)" required>
            <TextArea
              value={formData['Lesson Learned']}
              onChange={(e) => setFormData({ ...formData, 'Lesson Learned': e.target.value })}
              maxLength={500}
              required
            />
          </Field>

          <Field label="Recommendation (mandatory future action)" required>
            <TextArea
              value={formData.Recommendation}
              onChange={(e) => setFormData({ ...formData, Recommendation: e.target.value })}
              required
            />
          </Field>

          <Field label="Owner" required>
            <TextInput
              value={formData.Owner}
              onChange={(e) => setFormData({ ...formData, Owner: e.target.value })}
              required
            />
          </Field>

          <Field label="Keywords (optional)">
            <TextInput
              value={formData.Keywords}
              onChange={(e) => setFormData({ ...formData, Keywords: e.target.value })}
              placeholder="comma-separated tags"
            />
          </Field>

          <div className="flex flex-wrap gap-3 pt-4">
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save Lesson'}
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
