import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { api, Lesson, References } from '../lib/api'
import { lessonMatchesQuery } from '../lib/lessonSearch'
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
  const [phase, setPhase] = useState('')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [downloading, setDownloading] = useState<'html' | 'pdf' | null>(null)

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
    return lessons
      .filter((lesson) => {
        if (status && lesson.Status !== status) return false
        if (technicalBlock && lesson['Technical Block'] !== technicalBlock) return false
        if (phase && lesson['Project Phase'] !== phase) return false
        return lessonMatchesQuery(lesson, search)
      })
      .sort((a, b) => {
        const byModified = parseDate(b['Modified Date']) - parseDate(a['Modified Date'])
        if (byModified !== 0) return byModified
        return parseDate(b['Created Date']) - parseDate(a['Created Date'])
      })
  }, [lessons, search, status, technicalBlock, phase])

  const toggleExpanded = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const hasActiveFilters = Boolean(search || status || technicalBlock || phase)

  const clearFilters = () => {
    setSearch('')
    setStatus('')
    setTechnicalBlock('')
    setPhase('')
  }

  const downloadFiltered = async (kind: 'html' | 'pdf') => {
    const ids = filtered.map((lesson) => lesson['Lesson ID']).filter(Boolean)
    if (ids.length === 0) return
    setDownloading(kind)
    setError('')
    try {
      if (kind === 'html') await api.downloadHTML(ids)
      else await api.downloadPDF(ids)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download')
    } finally {
      setDownloading(null)
    }
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
              placeholder="Search all lesson fields"
              className="w-full"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="primary"
              disabled={filtered.length === 0 || downloading !== null}
              onClick={() => void downloadFiltered('html')}
            >
              {downloading === 'html' ? 'Downloading…' : 'Download HTML'}
            </Button>
            <Button
              variant="default"
              disabled={filtered.length === 0 || downloading !== null}
              onClick={() => void downloadFiltered('pdf')}
            >
              {downloading === 'pdf' ? 'Downloading…' : 'Download PDF'}
            </Button>
            {hasActiveFilters ? (
              <Button variant="ghost" onClick={clearFilters} className="shrink-0">
                Clear filters
              </Button>
            ) : null}
          </div>
        </div>

        {refs ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
                  <Meta label="Phase" value={lesson['Project Phase']} />
                  <Meta label="Owner" value={lesson.Owner} />
                  <Meta label="Implementation Owner" value={lesson['Implementation Owner']} />
                </dl>
                <div className="space-y-3 text-sm">
                  <p>
                    <span className="font-medium text-text">Event Description</span>
                    <span className="mt-1 block text-muted">
                      {open ? (lesson['Event Description']?.trim() || '—') : preview(lesson['Event Description'])}
                    </span>
                  </p>
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
