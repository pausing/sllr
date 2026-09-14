import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api, Lesson, References } from '../lib/api'
import { Card, Button, Select, StatusDot } from '../components/ui'

export function Lessons() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [filters, setFilters] = useState({
    technical_block: '',
    phase: '',
    status: '',
    category: '',
  })
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

  const handleFilter = () => {
    setLoading(true)
    api.getLessons(filters)
      .then(setLessons)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      await api.patchLesson(id, { Status: newStatus })
      const updated = await api.getLessons(filters)
      setLessons(updated)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  if (!refs) return <div className="text-muted">Loading...</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-text">Browse Lessons</h1>
        <Link to="/lessons/new">
          <Button variant="primary">Add New Lesson</Button>
        </Link>
      </div>

      <Card className="mb-6">
        <h3 className="text-lg font-medium text-text mb-4">Filters</h3>
        <div className="grid grid-cols-4 gap-4">
          <Select
            options={[{ value: '', label: 'All Technical Blocks' }, ...refs.technical_blocks.map(v => ({ value: v, label: v }))]}
            value={filters.technical_block}
            onChange={(e) => setFilters({ ...filters, technical_block: e.target.value })}
          />
          <Select
            options={[{ value: '', label: 'All Phases' }, ...refs.phases.map(v => ({ value: v, label: v }))]}
            value={filters.phase}
            onChange={(e) => setFilters({ ...filters, phase: e.target.value })}
          />
          <Select
            options={[{ value: '', label: 'All Statuses' }, ...refs.statuses.map(v => ({ value: v, label: v }))]}
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          />
          <Select
            options={[{ value: '', label: 'All Categories' }, ...refs.categories.map(v => ({ value: v, label: v }))]}
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          />
        </div>
        <Button variant="primary" onClick={handleFilter} className="mt-4">
          Apply Filters
        </Button>
      </Card>

      {loading ? (
        <div className="text-muted">Loading lessons...</div>
      ) : lessons.length === 0 ? (
        <Card>
          <p className="text-muted">No lessons found. Try adjusting your filters or add a new lesson.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {lessons.map((lesson) => (
            <Card key={lesson['Lesson ID']} className="hover:border-accent transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-accent font-mono text-sm">{lesson['Lesson ID']}</span>
                    <StatusDot status={lesson.Status} />
                  </div>
                  <h3 className="text-lg font-medium text-text mb-2">{lesson.Title}</h3>
                  <div className="flex gap-4 text-sm text-muted">
                    <span>{lesson['Project Phase']}</span>
                    <span>•</span>
                    <span>{lesson.Category}</span>
                    <span>•</span>
                    <span>{lesson['Technical Block']}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link to={`/lessons/${lesson['Lesson ID']}`}>
                    <Button variant="ghost">Edit</Button>
                  </Link>
                  {refs && (
                    <Select
                      options={refs.statuses.map(v => ({ value: v, label: v }))}
                      value={lesson.Status}
                      onChange={(e) => handleStatusChange(lesson['Lesson ID'], e.target.value)}
                      className="text-sm"
                    />
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
