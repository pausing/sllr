import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { Button, Card } from '../components/ui'
import { api, KPIs } from '../lib/api'

export function Dashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getKPIs()
      .then(setKpis)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading...</div>
  if (!kpis) return <div className="text-danger">Failed to load KPIs</div>

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-text md:text-3xl">Dashboard</h1>
        <div className="flex flex-wrap gap-2">
          <Link to="/lessons/new">
            <Button variant="primary">Add lesson learned</Button>
          </Link>
          <Link to="/lessons">
            <Button variant="default">Browse lessons learned</Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 mb-8 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <div className="text-2xl font-bold text-text">{kpis.total_lessons}</div>
          <div className="text-sm text-muted mt-1">Total Lessons</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-text">
            {kpis.capture_to_approval_days_avg?.toFixed(1) ?? '—'}
          </div>
          <div className="text-sm text-muted mt-1">Avg Capture→Approval (days)</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-text">{kpis.repeated_issues_count}</div>
          <div className="text-sm text-muted mt-1">Repeated Issues</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-text">{kpis.pct_implemented}%</div>
          <div className="text-sm text-muted mt-1">Recommendations Implemented</div>
        </Card>
        <Card>
          <div className="text-2xl font-bold text-text">{kpis.overdue_not_implemented_count}</div>
          <div className="text-sm text-muted mt-1">Overdue (Not Implemented)</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <BarChart title="By Status" data={kpis.by_status} />
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <BarChart title="By Technical Block" data={kpis.by_technical_block} />
          <BarChart title="By Implementation Status" data={kpis.by_implementation_status} />
        </div>
      </div>
    </div>
  )
}

function BarChart({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = Math.max(...entries.map(([, v]) => v), 1)

  if (entries.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-medium text-text mb-4">{title}</h3>
        <p className="text-sm text-muted">No data</p>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-lg font-medium text-text mb-4">{title}</h3>
      <div className="space-y-3">
        {entries.map(([label, value]) => (
          <div key={label}>
            <div className="flex justify-between gap-3 text-sm mb-1">
              <span className="min-w-0 truncate text-text">{label}</span>
              <span className="shrink-0 text-muted">{value}</span>
            </div>
            <div className="w-full h-2 bg-raised rounded">
              <div
                className="h-full bg-accent rounded"
                style={{ width: `${(value / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
