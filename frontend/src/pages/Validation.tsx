import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Card } from '../components/ui'

export function Validation() {
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getValidationReport()
      .then(setReport)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6 md:text-3xl">Validation</h1>
      
      <Card>
        <pre className="overflow-x-auto font-mono text-sm text-text whitespace-pre-wrap break-words">{report}</pre>
      </Card>
    </div>
  )
}
