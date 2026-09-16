import { useState } from 'react'
import { api } from '../lib/api'
import { Card, Button } from '../components/ui'

export function Export() {
  const [pdfLoading, setPdfLoading] = useState(false)
  const [htmlLoading, setHtmlLoading] = useState(false)
  const [error, setError] = useState('')

  const handlePDF = async () => {
    setPdfLoading(true)
    setError('')
    try {
      await api.downloadPDF()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate PDF')
    } finally {
      setPdfLoading(false)
    }
  }

  const handleHTML = async () => {
    setHtmlLoading(true)
    setError('')
    try {
      await api.downloadHTML()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate HTML')
    } finally {
      setHtmlLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6 md:text-3xl">Export</h1>
      
      <p className="text-muted mb-6">
        Generate PDF (phase → category, page breaks between categories) or HTML (expandable cards with filters).
      </p>

      {error && (
        <div className="mb-6 p-4 bg-danger/10 border border-danger rounded-md text-danger text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <h3 className="text-lg font-medium text-text mb-3">PDF Export</h3>
          <p className="text-sm text-muted mb-4">
            One section per <strong>Phase</strong>; within each phase, content ordered by{' '}
            <strong>Category</strong> → <strong>Technical Block</strong> → <strong>Sub-category</strong>,
            with a page break between categories.
          </p>
          <Button variant="primary" onClick={handlePDF} disabled={pdfLoading}>
            {pdfLoading ? 'Generating...' : 'Download PDF'}
          </Button>
        </Card>

        <Card>
          <h3 className="text-lg font-medium text-text mb-3">HTML Export</h3>
          <p className="text-sm text-muted mb-4">
            Single HTML file with <strong>expandable cards</strong> and <strong>filters</strong>{' '}
            (Phase, Category, Technical Block, Status). Open in any browser; no server needed.
          </p>
          <Button variant="primary" onClick={handleHTML} disabled={htmlLoading}>
            {htmlLoading ? 'Generating...' : 'Download HTML'}
          </Button>
        </Card>
      </div>
    </div>
  )
}
