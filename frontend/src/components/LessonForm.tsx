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
        <Field label="Category" required>
          <Select
            options={refs.categories.map((v) => ({ value: v, label: v }))}
            value={lesson.Category}
            onChange={(e) => onChange({ ...lesson, Category: e.target.value })}
            required
          />
        </Field>

        <Field label="Technical Block" required>
          <Select
            options={refs.technical_blocks.map((v) => ({ value: v, label: v }))}
            value={lesson['Technical Block']}
            onChange={(e) => onChange({ ...lesson, 'Technical Block': e.target.value })}
            required
          />
        </Field>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Sub-category" required>
          <TextInput
            value={lesson['Sub-category']}
            onChange={(e) => onChange({ ...lesson, 'Sub-category': e.target.value })}
            required
          />
        </Field>

        <Field label="Project Phase" required>
          <Select
            options={refs.phases.map((v) => ({ value: v, label: v }))}
            value={lesson['Project Phase']}
            onChange={(e) => onChange({ ...lesson, 'Project Phase': e.target.value })}
            required
          />
        </Field>
      </div>

      <Field label="Root Cause" required>
        <TextArea
          value={lesson['Root Cause']}
          onChange={(e) => onChange({ ...lesson, 'Root Cause': e.target.value })}
          required
        />
      </Field>

      <Field label="What Happened" required>
        <TextArea
          value={lesson['What Happened']}
          onChange={(e) => onChange({ ...lesson, 'What Happened': e.target.value })}
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
        <Field label="Recommendation Due Date">
          <TextInput
            type="date"
            value={lesson['Recommendation Due Date'] || ''}
            onChange={(e) => onChange({ ...lesson, 'Recommendation Due Date': e.target.value })}
          />
        </Field>

        <Field label="Owner" required>
          <TextInput
            value={lesson.Owner}
            onChange={(e) => onChange({ ...lesson, Owner: e.target.value })}
            required
          />
        </Field>
      </div>

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
