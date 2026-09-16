import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api, Approver, PortalMe, References } from '../lib/api'
import { Button, Card, TextInput } from '../components/ui'

export function Approvers() {
  const [me, setMe] = useState<PortalMe | null>(null)
  const [refs, setRefs] = useState<References | null>(null)
  const [approvers, setApprovers] = useState<Approver[]>([])
  const [loading, setLoading] = useState(true)
  const [email, setEmail] = useState('')
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    const [user, references, rows] = await Promise.all([
      api.getMe(),
      api.getReferences(),
      api.getApprovers(),
    ])
    setMe(user)
    setRefs(references)
    setApprovers(rows)
  }

  useEffect(() => {
    load()
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load approvers'))
      .finally(() => setLoading(false))
  }, [])

  const blocks = refs?.technical_blocks ?? []
  const isAdmin = me?.admin === true

  const sorted = useMemo(
    () => [...approvers].sort((a, b) => a.email.localeCompare(b.email)),
    [approvers],
  )

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault()
    const nextEmail = email.trim().toLowerCase()
    if (!nextEmail) return
    if (approvers.some((row) => row.email === nextEmail)) {
      setEmail('')
      return
    }
    setApprovers((current) => [...current, { email: nextEmail, technical_blocks: [] }])
    setEmail('')
  }

  const toggleBlock = async (row: Approver, block: string, checked: boolean) => {
    const next = checked
      ? [...row.technical_blocks, block]
      : row.technical_blocks.filter((item) => item !== block)
    setSaving(row.email)
    setError(null)
    try {
      const saved = await api.setApproverBlocks(row.email, next)
      setApprovers((current) =>
        current.map((item) => (item.email === saved.email ? saved : item)),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update blocks')
    } finally {
      setSaving(null)
    }
  }

  const handleRemove = async (row: Approver) => {
    if (!window.confirm(`Remove approver ${row.email}?`)) return
    setSaving(row.email)
    setError(null)
    try {
      if (row.technical_blocks.length > 0) {
        await api.deleteApprover(row.email)
      }
      setApprovers((current) => current.filter((item) => item.email !== row.email))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove approver')
    } finally {
      setSaving(null)
    }
  }

  if (loading) return <div className="text-muted">Loading...</div>

  if (!isAdmin) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-text mb-6">Approvers</h1>
        <p className="text-muted">Portal admin required to assign Technical Block approvers.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-text mb-6">Approvers</h1>
      <p className="text-muted mb-6">
        Assign which <strong>Technical Block(s)</strong> each portal user may approve.
        Emails should match portal login emails.
      </p>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <Card className="mb-8">
        <h3 className="text-lg font-medium text-text mb-4">Add user</h3>
        <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
          <div className="min-w-64 flex-1">
            <label className="mb-1 block text-sm font-medium text-text" htmlFor="approver-email">
              Portal email
            </label>
            <TextInput
              id="approver-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@powerlearn.us"
              className="w-full"
            />
          </div>
          <Button type="submit" variant="primary" disabled={!email.trim() || saving !== null}>
            Add user
          </Button>
        </form>
      </Card>

      <Card>
        <h3 className="text-lg font-medium text-text mb-4">Users and Technical Blocks</h3>
        {sorted.length === 0 ? (
          <p className="text-muted">No approvers yet. Add a portal user email above.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-muted">
                  <th className="py-2 pr-4 font-medium">Email</th>
                  {blocks.map((block) => (
                    <th key={block} className="py-2 px-2 font-medium whitespace-nowrap">
                      {block}
                    </th>
                  ))}
                  <th className="py-2 pl-4 font-medium" />
                </tr>
              </thead>
              <tbody>
                {sorted.map((row) => (
                  <tr key={row.email} className="border-b border-line last:border-0">
                    <td className="py-3 pr-4 font-mono text-accent">{row.email}</td>
                    {blocks.map((block) => (
                      <td key={block} className="py-3 px-2">
                        <input
                          type="checkbox"
                          className="accent-[#3dcc8c] h-4 w-4"
                          checked={row.technical_blocks.includes(block)}
                          disabled={saving === row.email}
                          onChange={(e) => toggleBlock(row, block, e.target.checked)}
                          aria-label={`${row.email} may approve ${block}`}
                        />
                      </td>
                    ))}
                    <td className="py-3 pl-4 text-right">
                      <Button
                        type="button"
                        variant="ghost"
                        className="text-danger"
                        disabled={saving === row.email}
                        onClick={() => handleRemove(row)}
                      >
                        Remove
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
