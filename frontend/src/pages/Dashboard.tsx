import { useEffect, useState } from 'react'
import { Card } from '../components/ui'
import { api, KPIs } from '../lib/api'

export function Dashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getKPIs()
      .then(setKpis)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading...</div>
  if (!kpis) return <div className="text-danger">Failed to load KPIs</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">Dashboard</h1>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-4 mb-8">
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

      {/* Charts */}
      <div className="grid grid-cols-1 gap-8">
        <BarChart title="By Status" data={kpis.by_status} />
        <div className="grid grid-cols-3 gap-6">
          <BarChart title="By Category" data={kpis.by_category} />
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
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text">{label}</span>
              <span className="text-muted">{value}</span>
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
