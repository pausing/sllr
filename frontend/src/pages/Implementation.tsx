import { useEffect, useState } from 'react'
import { api, Lesson, References } from '../lib/api'
import { Card, Select } from '../components/ui'

export function Implementation() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [refs, setRefs] = useState<References | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getReferences(), api.getLessons({ status: 'Approved' })])
      .then(([r, l]) => {
        setRefs(r)
        setLessons(l)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleImplStatusChange = async (id: string, newStatus: string) => {
    try {
      await api.patchLesson(id, { 'Implementation Status': newStatus })
      const updated = await api.getLessons({ status: 'Approved' })
      setLessons(updated)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update implementation status')
    }
  }

  if (loading) return <div className="text-muted">Loading...</div>
  if (!refs) return <div className="text-danger">Failed to load</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">Implementation Follow Up</h1>
      
      <p className="text-muted mb-6">
        Track implementation of recommendations for <strong>Approved</strong> lessons.
        Set <strong>Implementation Status</strong> to <strong>Implemented</strong> when the recommendation has been applied.
      </p>

      {lessons.length === 0 ? (
        <Card>
          <p className="text-muted">No approved lessons yet. Approve lessons first.</p>
        </Card>
      ) : (
        <Card>
          <h3 className="text-lg font-medium text-text mb-4">Approved Lessons</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left">
                  <th className="py-3 px-4 font-medium text-muted">Lesson ID</th>
                  <th className="py-3 px-4 font-medium text-muted">Title</th>
                  <th className="py-3 px-4 font-medium text-muted">Due Date</th>
                  <th className="py-3 px-4 font-medium text-muted">Owner</th>
                  <th className="py-3 px-4 font-medium text-muted">Implementation Status</th>
                </tr>
              </thead>
              <tbody>
                {lessons.map((lesson) => (
                  <tr key={lesson['Lesson ID']} className="border-b border-line hover:bg-raised">
                    <td className="py-3 px-4 font-mono text-blue">{lesson['Lesson ID']}</td>
                    <td className="py-3 px-4 text-text">{lesson.Title}</td>
                    <td className="py-3 px-4 text-muted">{lesson['Recommendation Due Date'] || '—'}</td>
                    <td className="py-3 px-4 text-muted">{lesson.Owner}</td>
                    <td className="py-3 px-4">
                      <Select
                        options={refs.implementation_statuses.map(v => ({ value: v, label: v }))}
                        value={lesson['Implementation Status']}
                        onChange={(e) => handleImplStatusChange(lesson['Lesson ID'], e.target.value)}
                        className="w-full"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
