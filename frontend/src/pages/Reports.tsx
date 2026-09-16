import { useState } from 'react'
import { api } from '../lib/api'
import { Card, Button } from '../components/ui'

export function Reports() {
  const [loading, setLoading] = useState<string | null>(null)

  const handleDownload = async (type: 'validation' | 'duplicates' | 'kpi' | 'csv') => {
    setLoading(type)
    try {
      if (type === 'validation') {
        const report = await api.getValidationReport()
        downloadText(report, 'validation_report.txt')
      } else if (type === 'duplicates') {
        const report = await api.getDuplicatesReport()
        downloadText(report, 'duplicates_report.txt')
      } else if (type === 'kpi') {
        const report = await api.getKPIReport()
        downloadText(report, 'kpi_report.txt')
      } else if (type === 'csv') {
        await api.downloadDashboardCSV()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Download failed')
    } finally {
      setLoading(null)
    }
  }

  const downloadText = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6 md:text-3xl">Reports</h1>
      
      <p className="text-muted mb-6">
        Generate and download validation, duplicates, KPI, and dashboard CSV reports.
      </p>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <h3 className="text-lg font-medium text-text mb-3">Validation Report</h3>
          <p className="text-sm text-muted mb-4">
            List all lessons with validation errors (missing required fields, invalid controlled values).
          </p>
          <Button
            variant="primary"
            onClick={() => handleDownload('validation')}
            disabled={loading === 'validation'}
          >
            {loading === 'validation' ? 'Downloading...' : 'Download validation_report.txt'}
          </Button>
        </Card>

        <Card>
          <h3 className="text-lg font-medium text-text mb-3">Duplicates Report</h3>
          <p className="text-sm text-muted mb-4">
            Find exact and near-duplicate lessons based on title similarity.
          </p>
          <Button
            variant="primary"
            onClick={() => handleDownload('duplicates')}
            disabled={loading === 'duplicates'}
          >
            {loading === 'duplicates' ? 'Downloading...' : 'Download duplicates_report.txt'}
          </Button>
        </Card>

        <Card>
          <h3 className="text-lg font-medium text-text mb-3">KPI Report</h3>
          <p className="text-sm text-muted mb-4">
            Governance KPIs: total lessons, repeated issues, capture-to-approval time, implementation %.
          </p>
          <Button
            variant="primary"
            onClick={() => handleDownload('kpi')}
            disabled={loading === 'kpi'}
          >
            {loading === 'kpi' ? 'Downloading...' : 'Download kpi_report.txt'}
          </Button>
        </Card>

        <Card>
          <h3 className="text-lg font-medium text-text mb-3">Dashboard CSV Export</h3>
          <p className="text-sm text-muted mb-4">
            Flat CSV with all lesson fields plus Validation_Errors column. For Power BI.
          </p>
          <Button
            variant="primary"
            onClick={() => handleDownload('csv')}
            disabled={loading === 'csv'}
          >
            {loading === 'csv' ? 'Downloading...' : 'Download dashboard_export.csv'}
          </Button>
        </Card>
      </div>
    </div>
  )
}
