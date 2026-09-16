import { FormEvent, useEffect, useState } from 'react'
import { api, ActivityEntry, PortalMe } from '../lib/api'
import { Button, Card, TextInput } from '../components/ui'

const PAGE_SIZE = 40

function formatLocalTime(iso: string): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function prettyValues(values: unknown): string {
  if (values == null) return ''
  try {
    return JSON.stringify(values, null, 2)
  } catch {
    return String(values)
  }
}

function changedLines(values: unknown): { field: string; before: unknown; after: unknown }[] {
  if (!values || typeof values !== 'object') return []
  const rec = values as { changed?: unknown }
  const changed = rec.changed
  if (!changed || typeof changed !== 'object') return []
  return Object.entries(changed as Record<string, { before?: unknown; after?: unknown }>).map(
    ([field, pair]) => ({
      field,
      before: pair?.before,
      after: pair?.after,
    }),
  )
}

export function Activity() {
  const [me, setMe] = useState<PortalMe | null>(null)
  const [items, setItems] = useState<ActivityEntry[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [action, setAction] = useState('')
  const [entityId, setEntityId] = useState('')
  const [since, setSince] = useState('')
  const [openId, setOpenId] = useState<number | null>(null)

  const filters = () => ({
    limit: PAGE_SIZE,
    email: email.trim() || undefined,
    action: action.trim() || undefined,
    entity_id: entityId.trim() || undefined,
    since: since.trim() || undefined,
  })

  const load = async (offset = 0, append = false) => {
    const page = await api.getActivity({ ...filters(), offset })
    setTotal(page.total)
    setItems((current) => (append ? [...current, ...page.items] : page.items))
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const user = await api.getMe()
        if (cancelled) return
        setMe(user)
        if (user?.admin !== true) return
        await load(0, false)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load activity')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
    // Initial load only; filters apply on submit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const isAdmin = me?.admin === true

  const handleFilter = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await load(0, false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activity')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadMore = async () => {
    setLoadingMore(true)
    setError(null)
    try {
      await load(items.length, true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load more')
    } finally {
      setLoadingMore(false)
    }
  }

  if (loading && items.length === 0) return <div className="text-muted">Loading...</div>

  if (!isAdmin) {
    return (
      <div>
        <h1 className="mb-2 text-2xl font-bold text-text md:text-3xl">Activity</h1>
        <p className="text-muted">Portal admin required to view the activity log.</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl">
      <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-accent">Administration</p>
      <h1 className="mb-2 text-2xl font-bold text-text md:text-3xl">Activity</h1>
      <p className="mb-6 max-w-2xl text-muted">
        Audit log of SLLR writes: who did what, when, and the values that changed.
      </p>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <Card className="mb-6">
        <form onSubmit={handleFilter} className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <TextInput
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-label="Filter by email"
          />
          <TextInput
            placeholder="Action (create_lesson…)"
            value={action}
            onChange={(event) => setAction(event.target.value)}
            aria-label="Filter by action"
          />
          <TextInput
            placeholder="Entity id"
            value={entityId}
            onChange={(event) => setEntityId(event.target.value)}
            aria-label="Filter by entity id"
          />
          <TextInput
            type="datetime-local"
            value={since}
            onChange={(event) => setSince(event.target.value)}
            aria-label="Since"
          />
          <Button type="submit" variant="primary">
            Filter
          </Button>
        </form>
      </Card>

      <p className="mb-3 text-sm text-muted">
        {total} {total === 1 ? 'event' : 'events'}
      </p>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-line text-muted">
              <th className="px-3 py-2 font-medium">Time</th>
              <th className="px-3 py-2 font-medium">User</th>
              <th className="px-3 py-2 font-medium">Action</th>
              <th className="px-3 py-2 font-medium">Entity</th>
              <th className="px-3 py-2 font-medium">Values</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => {
              const open = openId === row.id
              const diffs = changedLines(row.values)
              return (
                <tr key={row.id} className="border-b border-line align-top">
                  <td className="whitespace-nowrap px-3 py-3 text-text">{formatLocalTime(row.created_at)}</td>
                  <td className="px-3 py-3 text-text">{row.email || '—'}</td>
                  <td className="px-3 py-3 font-medium text-accent">{row.action}</td>
                  <td className="px-3 py-3 text-muted">
                    {row.entity_type}
                    {row.entity_id ? ` · ${row.entity_id}` : ''}
                  </td>
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      className="text-accent underline-offset-2 hover:underline"
                      onClick={() => setOpenId(open ? null : row.id)}
                    >
                      {open ? 'Hide' : 'Show'} values
                    </button>
                    {open ? (
                      <div className="mt-2 space-y-2">
                        {diffs.length > 0 ? (
                          <ul className="space-y-1 text-xs text-muted">
                            {diffs.map((diff) => (
                              <li key={diff.field}>
                                <span className="text-text">{diff.field}</span>:{' '}
                                <span>{String(diff.before ?? '—')}</span>
                                <span className="text-accent"> → </span>
                                <span>{String(diff.after ?? '—')}</span>
                              </li>
                            ))}
                          </ul>
                        ) : null}
                        <pre className="max-h-72 overflow-auto rounded-md border border-line bg-ink p-3 font-mono text-xs text-text">
                          {prettyValues(row.values)}
                        </pre>
                      </div>
                    ) : null}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="space-y-3 md:hidden">
        {items.map((row) => {
          const open = openId === row.id
          const diffs = changedLines(row.values)
          return (
            <Card key={row.id} className="overflow-x-auto">
              <p className="text-xs text-muted">{formatLocalTime(row.created_at)}</p>
              <p className="mt-1 font-medium text-accent">{row.action}</p>
              <p className="text-sm text-text">{row.email || '—'}</p>
              <p className="text-sm text-muted">
                {row.entity_type}
                {row.entity_id ? ` · ${row.entity_id}` : ''}
              </p>
              <button
                type="button"
                className="mt-2 text-sm text-accent underline-offset-2 hover:underline"
                onClick={() => setOpenId(open ? null : row.id)}
              >
                {open ? 'Hide values' : 'Show values'}
              </button>
              {open ? (
                <div className="mt-2 space-y-2">
                  {diffs.length > 0 ? (
                    <ul className="space-y-1 text-xs text-muted">
                      {diffs.map((diff) => (
                        <li key={diff.field}>
                          <span className="text-text">{diff.field}</span>:{' '}
                          {String(diff.before ?? '—')}
                          <span className="text-accent"> → </span>
                          {String(diff.after ?? '—')}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  <pre className="max-h-72 overflow-auto rounded-md border border-line bg-ink p-3 font-mono text-xs text-text">
                    {prettyValues(row.values)}
                  </pre>
                </div>
              ) : null}
            </Card>
          )
        })}
      </div>

      {items.length === 0 ? <p className="text-muted">No activity yet.</p> : null}

      {items.length < total ? (
        <div className="mt-6">
          <Button onClick={handleLoadMore} disabled={loadingMore}>
            {loadingMore ? 'Loading…' : 'Load more'}
          </Button>
        </div>
      ) : null}
    </div>
  )
}
