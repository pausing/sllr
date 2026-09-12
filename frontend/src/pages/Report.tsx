import { useEffect, useState } from 'react'
import { api, Lesson } from '../lib/api'
import { Card } from '../components/ui'

export function Report() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [loading, setLoading] = useState(true)
  const [htmlContent, setHtmlContent] = useState('')

  useEffect(() => {
    api.getLessons()
      .then((l) => {
        setLessons(l)
        // Fetch HTML report content
        return fetch('/api/export/html', { method: 'POST' })
      })
      .then((res) => res.text())
      .then(setHtmlContent)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading report...</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">View Report</h1>
      
      <Card className="p-0 overflow-hidden">
        <iframe
          srcDoc={htmlContent}
          className="w-full h-[800px] border-0"
          title="Lessons Learned Report"
        />
      </Card>
    </div>
  )
}
