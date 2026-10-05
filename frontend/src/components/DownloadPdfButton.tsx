import { useState } from 'react'
import { api } from '../lib/api'
import { Button } from './ui'

export function DownloadPdfButton({
  ids,
  variant = 'default',
  label = 'Download PDF',
  className = '',
}: {
  ids?: string[]
  variant?: 'default' | 'primary' | 'ghost'
  label?: string
  className?: string
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const handle = async () => {
    setBusy(true)
    setError('')
    try {
      await api.downloadPDF(ids)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download PDF')
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <Button type="button" variant={variant} disabled={busy} onClick={() => void handle()} className={className}>
        {busy ? 'Downloading…' : label}
      </Button>
      {error ? <span className="text-sm text-danger">{error}</span> : null}
    </span>
  )
}
