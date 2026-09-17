import { FormEvent } from 'react'
import { Lesson, References } from '../lib/api'
import { Button, Field, TextInput, TextArea, Select } from './ui'

interface LessonFormProps {
  lesson: Lesson
  refs: References
  error?: string
  loading?: boolean
  onChange: (lesson: Lesson) => void
  onSubmit: (e: FormEvent) => void
  onCancel: () => void
}

export function LessonForm({
  lesson,
  refs,
  error,
  loading,
  onChange,
  onSubmit,
  onCancel,
}: LessonFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-6">
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
          onChange={(e) => onChange({ ...lesson, Title: e.target.value })}
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
            options={refs.technical_blocks.map((v) => ({ value: v, label: v }))}
            value={lesson['Technical Block']}
            onChange={(e) => onChange({ ...lesson, 'Technical Block': e.target.value })}
            required
          />
        </Field>

        <Field
          label="Project Phase"
          required
          hint="The point in the project life cycle where the solution must be implemented to prevent recurrence. A lesson found late (e.g. at commissioning) is often solved earlier (e.g. in design or procurement) — pick the phase where the action lands."
        >
          <Select
            options={refs.phases.map((v) => ({ value: v, label: v }))}
            value={lesson['Project Phase']}
            onChange={(e) => onChange({ ...lesson, 'Project Phase': e.target.value })}
            required
          />
        </Field>
      </div>

      <Field label="Event Description" required>
        <TextArea
          value={lesson['Event Description']}
          onChange={(e) => onChange({ ...lesson, 'Event Description': e.target.value })}
          required
        />
      </Field>

      <Field label="Root Cause" required>
        <TextArea
          value={lesson['Root Cause']}
          onChange={(e) => onChange({ ...lesson, 'Root Cause': e.target.value })}
          required
        />
      </Field>

      <Field label="Impact" required>
        <TextInput
          value={lesson.Impact}
          onChange={(e) => onChange({ ...lesson, Impact: e.target.value })}
          required
        />
      </Field>

      <Field label="Lesson Learned" required>
        <TextArea
          value={lesson['Lesson Learned']}
          onChange={(e) => onChange({ ...lesson, 'Lesson Learned': e.target.value })}
          maxLength={500}
          required
        />
      </Field>

      <Field label="Recommendation" required>
        <TextArea
          value={lesson.Recommendation}
          onChange={(e) => onChange({ ...lesson, Recommendation: e.target.value })}
          required
        />
      </Field>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Implementation Owner">
          <TextInput
            type="email"
            value={lesson['Implementation Owner'] || ''}
            onChange={(e) => onChange({ ...lesson, 'Implementation Owner': e.target.value })}
          />
        </Field>

        <Field label="Implementation Due Date">
          <TextInput
            type="date"
            value={lesson['Implementation Due Date'] || ''}
            onChange={(e) => onChange({ ...lesson, 'Implementation Due Date': e.target.value })}
          />
        </Field>
      </div>

      <Field label="Owner" required>
        <TextInput
          value={lesson.Owner}
          onChange={(e) => onChange({ ...lesson, Owner: e.target.value })}
          required
        />
      </Field>

      <Field label="Keywords">
        <TextInput
          value={lesson.Keywords || ''}
          onChange={(e) => onChange({ ...lesson, Keywords: e.target.value })}
        />
      </Field>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Status" required>
          <Select
            options={refs.statuses.map((v) => ({ value: v, label: v }))}
            value={lesson.Status}
            onChange={(e) => onChange({ ...lesson, Status: e.target.value })}
            required
          />
        </Field>

        <Field label="Implementation Status" required>
          <Select
            options={refs.implementation_statuses.map((v) => ({ value: v, label: v }))}
            value={lesson['Implementation Status']}
            onChange={(e) => onChange({ ...lesson, 'Implementation Status': e.target.value })}
            required
          />
        </Field>
      </div>

      <div className="flex flex-wrap gap-3 pt-4">
        <Button type="submit" variant="primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
