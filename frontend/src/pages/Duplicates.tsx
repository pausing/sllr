import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Card } from '../components/ui'

export function Duplicates() {
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getDuplicatesReport()
      .then(setReport)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading...</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">Duplicates</h1>
      
      <Card>
        <pre className="font-mono text-sm text-text whitespace-pre-wrap">{report}</pre>
      </Card>
    </div>
  )
}
