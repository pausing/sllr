import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { api, References } from '../lib/api'
import { Card, Button, Field, TextInput, TextArea, Select } from '../components/ui'

export function LessonNew() {
  const navigate = useNavigate()
  const [refs, setRefs] = useState<References | null>(null)
  const [nextId, setNextId] = useState('')
  const [formData, setFormData] = useState({
    'Lesson ID': '',
    Title: '',
    Category: '',
    'Technical Block': '',
    'Sub-category': '',
    'Project Phase': '',
    'Root Cause': '',
    'What Happened': '',
    Impact: '',
    'Lesson Learned': '',
    Recommendation: '',
    'Recommendation Due Date': '',
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
        setFormData(f => ({
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
            <Field label="Category" required>
              <Select
                options={[{ value: '', label: 'Select...' }, ...refs.categories.map(v => ({ value: v, label: v }))]}
                value={formData.Category}
                onChange={(e) => setFormData({ ...formData, Category: e.target.value })}
                required
              />
            </Field>

            <Field label="Technical Block" required>
              <Select
                options={[{ value: '', label: 'Select...' }, ...refs.technical_blocks.map(v => ({ value: v, label: v }))]}
                value={formData['Technical Block']}
                onChange={(e) => setFormData({ ...formData, 'Technical Block': e.target.value })}
                required
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Sub-category" required>
              <TextInput
                value={formData['Sub-category']}
                onChange={(e) => setFormData({ ...formData, 'Sub-category': e.target.value })}
                required
              />
            </Field>

            <Field label="Project Phase" required>
              <Select
                options={[{ value: '', label: 'Select...' }, ...refs.phases.map(v => ({ value: v, label: v }))]}
                value={formData['Project Phase']}
                onChange={(e) => setFormData({ ...formData, 'Project Phase': e.target.value })}
                required
              />
            </Field>
          </div>

          <Field label="Root Cause" required>
            <TextArea
              value={formData['Root Cause']}
              onChange={(e) => setFormData({ ...formData, 'Root Cause': e.target.value })}
              required
            />
          </Field>

          <Field label="What Happened" required>
            <TextArea
              value={formData['What Happened']}
              onChange={(e) => setFormData({ ...formData, 'What Happened': e.target.value })}
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

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Recommendation Due Date">
              <TextInput
                type="date"
                value={formData['Recommendation Due Date']}
                onChange={(e) => setFormData({ ...formData, 'Recommendation Due Date': e.target.value })}
              />
            </Field>

            <Field label="Owner" required>
              <TextInput
                value={formData.Owner}
                onChange={(e) => setFormData({ ...formData, Owner: e.target.value })}
                required
              />
            </Field>
          </div>

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
