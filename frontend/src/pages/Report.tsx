import { useEffect, useState } from 'react'
import { Card } from '../components/ui'

export function Report() {
  const [loading, setLoading] = useState(true)
  const [htmlContent, setHtmlContent] = useState('')

  useEffect(() => {
    // Fetch HTML report content
    fetch('/api/export/html', { method: 'POST' })
      .then((res) => res.text())
      .then(setHtmlContent)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading report...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6 md:text-3xl">View Report</h1>
      
      <Card className="p-0 overflow-hidden">
        <iframe
          srcDoc={htmlContent}
          className="w-full h-[70vh] border-0 md:h-[800px]"
          title="Lessons Learned Report"
        />
      </Card>
    </div>
  )
}
