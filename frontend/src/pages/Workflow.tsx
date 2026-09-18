import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { Button, Select, TextInput } from '../components/ui'
import { api, Lesson, References } from '../lib/api'
import { lessonPath } from '../lib/lessonAccess'
import {
  BOARD_STAGE_CLASSES,
  BOARD_STAGE_LEGEND,
  BOARD_STAGES,
  BoardStage,
  filterWorkflowLessons,
  groupLessonsByBlock,
  lessonBoardStage,
} from '../lib/workflowBoard'

export function Workflow() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [technicalBlock, setTechnicalBlock] = useState('')
  const [phase, setPhase] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    let cancelled = false
    Promise.all([api.getReferences(), api.getLessons()])
      .then(([r, l]) => {
        if (cancelled) return
        setRefs(r)
        setLessons(l)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load lessons')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const visible = useMemo(
    () =>
      filterWorkflowLessons(lessons, {
        status,
        technical_block: technicalBlock,
        phase,
        q: search,
      }),
    [lessons, status, technicalBlock, phase, search],
  )

  const lanes = useMemo(
    () => groupLessonsByBlock(visible, refs?.technical_blocks ?? [], technicalBlock),
    [visible, refs, technicalBlock],
  )

  if (loading && !refs) return <div className="text-muted">Loading...</div>

  return (
    <div className="workflow-canvas -m-4 flex min-h-[calc(100vh-2.75rem)] flex-col p-4 md:-m-8 md:p-8">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text md:text-3xl">Workflow</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Status board of lessons by Technical Block. Cards use the same records as Browse; click a
            card to open View.
          </p>
        </div>
        <p className="text-sm text-muted">
          {visible.length} of {lessons.length} lessons
        </p>
      </div>

      <section
        aria-label="Status color legend"
        className="mb-4 rounded-xl border border-line/80 bg-panel/80 px-3 py-3 backdrop-blur-sm"
      >
        <h2 className="mb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-muted">Legend</h2>
        <ul className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-x-6 sm:gap-y-2">
          {BOARD_STAGE_LEGEND.map((item) => (
            <li key={item.stage} className="flex min-w-0 items-start gap-2 text-sm">
              <span
                className={`mt-1 inline-block h-2.5 w-2.5 shrink-0 rounded-full ${BOARD_STAGE_CLASSES[item.stage].pip}`}
                aria-hidden="true"
              />
              <span>
                <span className="font-medium text-text">{item.stage}</span>
                <span className="text-muted">
                  {' '}
                  — {item.meaning} ({item.token} {item.color})
                </span>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-text">Search</span>
          <TextInput
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search all lesson fields"
            className="bg-panel/90"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-text">Technical Block</span>
          <Select
            className="bg-panel/90"
            options={[
              { value: '', label: 'All Technical Blocks' },
              ...(refs?.technical_blocks ?? []).map((v) => ({ value: v, label: v })),
            ]}
            value={technicalBlock}
            onChange={(e) => setTechnicalBlock(e.target.value)}
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-text">Phase</span>
          <Select
            className="bg-panel/90"
            options={[
              { value: '', label: 'All Phases' },
              ...(refs?.phases ?? []).map((v) => ({ value: v, label: v })),
            ]}
            value={phase}
            onChange={(e) => setPhase(e.target.value)}
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-text">Status</span>
          <Select
            className="bg-panel/90"
            options={[
              { value: '', label: 'All Statuses' },
              ...(refs?.statuses ?? []).map((v) => ({ value: v, label: v })),
            ]}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          />
        </label>
      </div>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      {loading ? (
        <p className="text-muted">Loading lessons...</p>
      ) : lessons.length === 0 ? (
        <div className="rounded-xl border border-line bg-panel/80 p-6">
          <p className="text-muted">No lessons yet.</p>
          <Link to="/lessons/new" className="mt-3 inline-block">
            <Button variant="primary">Add lesson</Button>
          </Link>
        </div>
      ) : visible.length === 0 ? (
        <div className="rounded-xl border border-line bg-panel/80 p-6">
          <p className="text-muted">No lessons match these filters.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:gap-4 md:overflow-x-auto md:pb-2">
          {lanes.map((lane) => (
            <section
              key={lane.block}
              className="flex w-full shrink-0 flex-col md:w-[18.5rem]"
              aria-label={`${lane.block} technical block`}
            >
              <header className="mb-3 flex items-center justify-between gap-2 rounded-lg border border-line/80 bg-panel/70 px-3 py-2">
                <h2 className="truncate text-sm font-semibold text-text">{lane.block}</h2>
                <span className="shrink-0 rounded-full border border-line px-2 py-0.5 font-mono text-[11px] text-muted">
                  {lane.lessons.length}
                </span>
              </header>
              <div className="flex flex-col gap-3">
                {lane.lessons.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-line/80 px-3 py-6 text-center text-sm text-muted">
                    No cards
                  </p>
                ) : (
                  lane.lessons.map((lesson) => <WorkflowCard key={lesson['Lesson ID']} lesson={lesson} />)
                )}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}

function WorkflowCard({ lesson }: { lesson: Lesson }) {
  const id = lesson['Lesson ID']
  const stage = lessonBoardStage(lesson)
  const chrome = BOARD_STAGE_CLASSES[stage]
  const block = (lesson['Technical Block'] ?? '').trim() || 'Unassigned'
  const owner = (lesson.Owner ?? '').trim() || '—'
  const phase = (lesson['Project Phase'] ?? '').trim() || '—'

  return (
    <Link
      to={lessonPath(id)}
      className={`group block rounded-xl border bg-raised/95 p-3 transition-colors hover:bg-raised focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${chrome.border} ${chrome.glow}`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <span className="rounded-md border border-line/80 bg-panel/80 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted">
          {block}
        </span>
        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${chrome.chip}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${chrome.pip}`} aria-hidden="true" />
          {stage}
        </span>
      </div>
      <h3 className="text-[15px] font-semibold leading-snug text-text group-hover:text-accent">{lesson.Title}</h3>
      <p className="mt-2 flex flex-wrap gap-x-2 gap-y-0.5 font-mono text-[11px] text-muted">
        <span>{id}</span>
        <span aria-hidden="true">·</span>
        <span className="max-w-[11rem] truncate" title={owner}>
          {owner}
        </span>
        <span aria-hidden="true">·</span>
        <span>{phase}</span>
      </p>
      <StagePips stage={stage} />
    </Link>
  )
}

function StagePips({ stage }: { stage: BoardStage }) {
  const current = BOARD_STAGES.indexOf(stage)
  return (
    <div className="mt-3 flex items-center gap-1" aria-label={`Progress: ${stage}`}>
      {BOARD_STAGES.map((step, index) => {
        const reached = index <= current
        const classes = BOARD_STAGE_CLASSES[step]
        return (
          <span key={step} className="flex items-center gap-1">
            <span
              className={`h-1.5 w-1.5 rounded-full ${reached ? classes.pip : 'bg-line'}`}
              title={step}
            />
            {index < BOARD_STAGES.length - 1 ? (
              <span className={`h-px w-4 ${index < current ? classes.bar : 'bg-line'}`} aria-hidden="true" />
            ) : null}
          </span>
        )
      })}
    </div>
  )
}
