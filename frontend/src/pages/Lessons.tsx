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
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-text md:text-3xl">Browse Lessons</h1>
        <Link to="/lessons/new" className="shrink-0">
          <Button variant="primary">Add New Lesson</Button>
        </Link>
      </div>

      <Card className="mb-6">
        <h3 className="text-lg font-medium text-text mb-4">Filters</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex flex-wrap items-center gap-3">
                    <span className="text-accent font-mono text-sm">{lesson['Lesson ID']}</span>
                    <StatusDot status={lesson.Status} />
                  </div>
                  <h3 className="text-lg font-medium text-text mb-2">{lesson.Title}</h3>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
                    <span>{lesson['Project Phase']}</span>
                    <span className="hidden sm:inline">•</span>
                    <span>{lesson.Category}</span>
                    <span className="hidden sm:inline">•</span>
                    <span>{lesson['Technical Block']}</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 sm:shrink-0">
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
