import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router'
import { DeleteLessonButton, deletedLessonNotice } from '../components/DeleteLessonButton'
import { Card, Button, Select, StatusDot, TextInput } from '../components/ui'
import { api, Lesson, PortalMe, References } from '../lib/api'
import { canDeleteLesson, canEditLesson, lessonPath } from '../lib/lessonAccess'
import { lessonMatchesQuery } from '../lib/lessonSearch'

export function Lessons() {
  const location = useLocation()
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [me, setMe] = useState<PortalMe | null>(null)
  const [notice, setNotice] = useState('')
  const [filters, setFilters] = useState({
    technical_block: '',
    phase: '',
    status: '',
  })
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const state = location.state as { notice?: string } | null
    if (state?.notice) setNotice(state.notice)
  }, [location.state])

  useEffect(() => {
    Promise.all([api.getReferences(), api.getLessons(), api.getMe().catch(() => null)])
      .then(([r, l, user]) => {
        setRefs(r)
        setLessons(l)
        setMe(user)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleFilter = () => {
    setLoading(true)
    api
      .getLessons({ ...filters, q: search })
      .then(setLessons)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const visible = useMemo(
    () => lessons.filter((lesson) => lessonMatchesQuery(lesson, search)),
    [lessons, search],
  )

  if (!refs) return <div className="text-muted">Loading...</div>

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-text md:text-3xl">Browse Lessons</h1>
        <Link to="/lessons/new" className="shrink-0">
          <Button variant="primary">Add New Lesson</Button>
        </Link>
      </div>

      {notice ? (
        <div className="mb-4 rounded-md border border-accent/40 bg-accent-dim px-3 py-2 text-sm text-text" role="status">
          {notice}
        </div>
      ) : null}

      <Card className="mb-6">
        <h3 className="text-lg font-medium text-text mb-4">Filters</h3>
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-text" htmlFor="browse-search">
            Search
          </label>
          <TextInput
            id="browse-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search all lesson fields"
            className="w-full"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Select
            options={[
              { value: '', label: 'All Technical Blocks' },
              ...refs.technical_blocks.map((v) => ({ value: v, label: v })),
            ]}
            value={filters.technical_block}
            onChange={(e) => setFilters({ ...filters, technical_block: e.target.value })}
          />
          <Select
            options={[
              { value: '', label: 'All Phases' },
              ...refs.phases.map((v) => ({ value: v, label: v })),
            ]}
            value={filters.phase}
            onChange={(e) => setFilters({ ...filters, phase: e.target.value })}
          />
          <Select
            options={[
              { value: '', label: 'All Statuses' },
              ...refs.statuses.map((v) => ({ value: v, label: v })),
            ]}
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          />
        </div>
        <Button variant="primary" onClick={handleFilter} className="mt-4">
          Apply Filters
        </Button>
      </Card>

      {loading ? (
        <div className="text-muted">Loading lessons...</div>
      ) : visible.length === 0 ? (
        <Card>
          <p className="text-muted">No lessons found. Try adjusting your filters or add a new lesson.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {visible.map((lesson) => {
            const id = lesson['Lesson ID']
            const href = lessonPath(id)
            const showEdit = canEditLesson(me, lesson.Owner)
            const showDelete = canDeleteLesson(me, lesson)
            return (
              <Card key={id} className="hover:border-accent transition-colors">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <Link
                    to={href}
                    className="min-w-0 flex-1 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-3">
                      <span className="text-accent font-mono text-sm">{id}</span>
                      <StatusDot status={lesson.Status} />
                    </div>
                    <h3 className="text-lg font-medium text-text mb-2 hover:text-accent">{lesson.Title}</h3>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
                      <span>{lesson['Project Phase']}</span>
                      <span className="hidden sm:inline">•</span>
                      <span>{lesson['Technical Block']}</span>
                    </div>
                  </Link>
                  <div className="flex flex-wrap gap-2 sm:shrink-0">
                    <Link to={href}>
                      <Button variant="primary">View</Button>
                    </Link>
                    {showEdit ? (
                      <Link to={lessonPath(id, true)}>
                        <Button variant="ghost">Edit</Button>
                      </Link>
                    ) : null}
                    {showDelete ? (
                      <DeleteLessonButton
                        lesson={lesson}
                        onDeleted={(removed) => {
                          setLessons((current) =>
                            current.filter((row) => row['Lesson ID'] !== removed['Lesson ID']),
                          )
                          setNotice(deletedLessonNotice(removed))
                        }}
                      />
                    ) : null}
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
