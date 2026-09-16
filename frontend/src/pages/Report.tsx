import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { api, Lesson, References } from '../lib/api'
import { Button, Card, Select, StatusDot, TextInput } from '../components/ui'

function parseDate(value?: string): number {
  if (!value) return 0
  const t = Date.parse(value)
  return Number.isNaN(t) ? 0 : t
}

function preview(text: string | undefined, max = 180): string {
  const value = (text ?? '').replace(/\s+/g, ' ').trim()
  if (!value) return '—'
  if (value.length <= max) return value
  return `${value.slice(0, max).trimEnd()}…`
}

function isTruncated(text: string | undefined, max = 180): boolean {
  return (text ?? '').replace(/\s+/g, ' ').trim().length > max
}

export function Report() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [technicalBlock, setTechnicalBlock] = useState('')
  const [category, setCategory] = useState('')
  const [phase, setPhase] = useState('')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const load = () => {
    setLoading(true)
    setError('')
    Promise.all([api.getReferences(), api.getLessons()])
      .then(([r, l]) => {
        setRefs(r)
        setLessons(Array.isArray(l) ? l : [])
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load lessons')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return lessons
      .filter((lesson) => {
        if (status && lesson.Status !== status) return false
        if (technicalBlock && lesson['Technical Block'] !== technicalBlock) return false
        if (category && lesson.Category !== category) return false
        if (phase && lesson['Project Phase'] !== phase) return false
        if (q) {
          const id = (lesson['Lesson ID'] ?? '').toLowerCase()
          const title = (lesson.Title ?? '').toLowerCase()
          if (!id.includes(q) && !title.includes(q)) return false
        }
        return true
      })
      .sort((a, b) => {
        const byModified = parseDate(b['Modified Date']) - parseDate(a['Modified Date'])
        if (byModified !== 0) return byModified
        return parseDate(b['Created Date']) - parseDate(a['Created Date'])
      })
  }, [lessons, search, status, technicalBlock, category, phase])

  const toggleExpanded = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const hasActiveFilters = Boolean(search || status || technicalBlock || category || phase)

  const clearFilters = () => {
    setSearch('')
    setStatus('')
    setTechnicalBlock('')
    setCategory('')
    setPhase('')
  }

  return (
    <div className="report-gallery">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text md:text-3xl">View Report</h1>
        <p className="mt-1 text-sm text-muted">All lessons</p>
      </div>

      <Card className="mb-6 print:hidden">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0 flex-1">
            <label className="mb-1 block text-sm font-medium text-text" htmlFor="report-search">
              Search
            </label>
            <TextInput
              id="report-search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Title or Lesson ID"
              className="w-full"
            />
          </div>
          {hasActiveFilters ? (
            <Button variant="ghost" onClick={clearFilters} className="shrink-0">
              Clear filters
            </Button>
          ) : null}
        </div>

        {refs ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Select
              aria-label="Status"
              options={[{ value: '', label: 'All Statuses' }, ...refs.statuses.map((v) => ({ value: v, label: v }))]}
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            />
            <Select
              aria-label="Technical Block"
              options={[
                { value: '', label: 'All Technical Blocks' },
                ...refs.technical_blocks.map((v) => ({ value: v, label: v })),
              ]}
              value={technicalBlock}
              onChange={(e) => setTechnicalBlock(e.target.value)}
            />
            <Select
              aria-label="Category"
              options={[{ value: '', label: 'All Categories' }, ...refs.categories.map((v) => ({ value: v, label: v }))]}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
            <Select
              aria-label="Phase"
              options={[{ value: '', label: 'All Phases' }, ...refs.phases.map((v) => ({ value: v, label: v }))]}
              value={phase}
              onChange={(e) => setPhase(e.target.value)}
            />
          </div>
        ) : null}

        {!loading && !error ? (
          <p className="mt-4 text-sm text-muted">
            Showing {filtered.length} of {lessons.length} lesson{lessons.length === 1 ? '' : 's'}
          </p>
        ) : null}
      </Card>

      {loading ? (
        <div className="text-muted">Loading lessons...</div>
      ) : error ? (
        <Card>
          <p className="text-danger">{error}</p>
          <Button variant="primary" onClick={load} className="mt-4">
            Retry
          </Button>
        </Card>
      ) : filtered.length === 0 ? (
        <Card>
          <p className="text-muted">
            {lessons.length === 0
              ? 'No lessons yet.'
              : 'No lessons match these filters. Try a different search or clear filters.'}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((lesson) => {
            const id = lesson['Lesson ID']
            const open = Boolean(expanded[id])
            const learned = lesson['Lesson Learned']
            const recommendation = lesson.Recommendation
            const canExpand = isTruncated(learned) || isTruncated(recommendation)

            return (
              <Card
                key={id}
                className="flex flex-col print:break-inside-avoid hover:border-accent transition-colors"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm text-accent">{id}</span>
                  <StatusDot status={lesson.Status || '—'} />
                  {lesson['Implementation Status'] ? (
                    <StatusDot status={lesson['Implementation Status']} />
                  ) : null}
                </div>
                <h3 className="mb-3 text-lg font-medium text-text">{lesson.Title || 'Untitled'}</h3>
                <dl className="mb-4 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                  <Meta label="Technical Block" value={lesson['Technical Block']} />
                  <Meta label="Category" value={lesson.Category} />
                  <Meta label="Phase" value={lesson['Project Phase']} />
                  <Meta label="Owner" value={lesson.Owner} />
                </dl>
                <div className="space-y-3 text-sm">
                  <p>
                    <span className="font-medium text-text">Lesson Learned</span>
                    <span className="mt-1 block text-muted">
                      {open ? (learned?.trim() || '—') : preview(learned)}
                    </span>
                  </p>
                  <p>
                    <span className="font-medium text-text">Recommendation</span>
                    <span className="mt-1 block text-muted">
                      {open ? (recommendation?.trim() || '—') : preview(recommendation)}
                    </span>
                  </p>
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-2 print:hidden">
                  {canExpand ? (
                    <Button variant="ghost" onClick={() => toggleExpanded(id)} className="px-3 py-1 text-sm">
                      {open ? 'Show less' : 'Show more'}
                    </Button>
                  ) : null}
                  <Link to={`/lessons/${encodeURIComponent(id)}`} className="text-sm text-accent hover:underline">
                    Open lesson
                  </Link>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

function Meta({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
      <dd className="text-text">{value?.trim() || '—'}</dd>
    </div>
  )
}
