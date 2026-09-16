import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api, ApproverBlock, PortalMe, SllrUser } from '../lib/api'
import { Button, Card, Select, TextInput } from '../components/ui'

export function Approvers() {
  const [me, setMe] = useState<PortalMe | null>(null)
  const [blocks, setBlocks] = useState<ApproverBlock[]>([])
  const [portalUsers, setPortalUsers] = useState<SllrUser[]>([])
  const [portalAvailable, setPortalAvailable] = useState(false)
  const [extraEmails, setExtraEmails] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [typedEmail, setTypedEmail] = useState('')
  const [pickedUser, setPickedUser] = useState('')
  const [secondary, setSecondary] = useState<Record<string, string>>({})

  const load = async () => {
    const user = await api.getMe()
    setMe(user)
    if (user?.admin !== true) return
    const [payload, portal] = await Promise.all([api.getApprovers(), api.getPortalSllrUsers()])
    setBlocks(payload.blocks)
    setPortalUsers(portal.users)
    setPortalAvailable(portal.available)
  }

  useEffect(() => {
    load()
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load approvers'))
      .finally(() => setLoading(false))
  }, [])

  const isAdmin = me?.admin === true
  const mappedEmails = useMemo(
    () => blocks.flatMap((row) => row.emails),
    [blocks],
  )

  const candidates = useMemo(() => {
    const names = new Map<string, string | null>()
    for (const user of portalUsers) {
      names.set(user.email, user.name ?? null)
    }
    const emails = new Set<string>([
      ...portalUsers.map((user) => user.email),
      ...extraEmails,
      ...mappedEmails,
    ])
    return [...emails]
      .sort((a, b) => a.localeCompare(b))
      .map((email) => ({ email, name: names.get(email) ?? null }))
  }, [portalUsers, extraEmails, mappedEmails])

  const addEmailToCandidates = (raw: string) => {
    const email = raw.trim().toLowerCase()
    if (!email || !email.includes('@')) {
      setError('Enter a valid email address.')
      return
    }
    setError(null)
    setExtraEmails((current) => (current.includes(email) ? current : [...current, email]))
    setTypedEmail('')
    setPickedUser('')
  }

  const handleAddTyped = (event: FormEvent) => {
    event.preventDefault()
    addEmailToCandidates(typedEmail)
  }

  const applyBlock = async (technicalBlock: string, emails: string[]) => {
    setSaving(technicalBlock)
    setError(null)
    try {
      const saved = await api.setBlockApprovers(technicalBlock, emails)
      setBlocks((current) =>
        current.map((row) => (row.technical_block === saved.technical_block ? saved : row)),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update approver')
    } finally {
      setSaving(null)
    }
  }

  const handlePrimaryChange = (block: string, email: string) => {
    void applyBlock(block, email ? [email] : [])
  }

  const handleAlsoApprove = async (block: string) => {
    const email = (secondary[block] || '').trim().toLowerCase()
    if (!email) return
    const row = blocks.find((item) => item.technical_block === block)
    if (row?.emails.includes(email)) {
      setSecondary((current) => ({ ...current, [block]: '' }))
      return
    }
    setSaving(block)
    setError(null)
    try {
      const saved = await api.addBlockApprover(block, email)
      setBlocks((current) =>
        current.map((item) => (item.technical_block === saved.technical_block ? saved : item)),
      )
      setSecondary((current) => ({ ...current, [block]: '' }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add secondary approver')
    } finally {
      setSaving(null)
    }
  }

  const handleRemoveEmail = async (block: string, email: string) => {
    const row = blocks.find((item) => item.technical_block === block)
    const next = (row?.emails || []).filter((item) => item !== email)
    await applyBlock(block, next)
  }

  if (loading) return <div className="text-muted">Loading...</div>

  if (!isAdmin) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-text mb-2">Approvers</h1>
        <p className="text-muted">Portal admin required to assign Technical Block approvers.</p>
      </div>
    )
  }

  const selectOptions = [
    { value: '', label: 'Unassigned' },
    ...candidates.map((user) => ({
      value: user.email,
      label: user.name ? `${user.name} (${user.email})` : user.email,
    })),
  ]

  const portalOptions = portalUsers
    .filter((user) => !extraEmails.includes(user.email))
    .map((user) => ({
      value: user.email,
      label: user.name ? `${user.name} (${user.email})` : user.email,
    }))

  return (
    <div className="max-w-4xl">
      <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-accent">Administration</p>
      <h1 className="mb-2 text-3xl font-bold text-text">Approvers</h1>
      <p className="mb-8 max-w-2xl text-muted">
        Assign one primary approver for each Technical Block. The selected person may set lessons
        in that block from Draft to Approved. Choose from people who already have SLLR access.
      </p>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <Card className="mb-8">
        <h2 className="mb-1 text-lg font-medium text-text">Add user</h2>
        <p className="mb-4 text-sm text-muted">
          {portalAvailable && portalUsers.length > 0
            ? 'Pick someone who already has SLLR access, or type an email if they are not in the list yet. Users are not invented automatically.'
            : 'Portal user list is unavailable. Type the portal login email to add a candidate. Do not invent accounts.'}
        </p>
        <div className="flex flex-col gap-4">
          {portalOptions.length > 0 ? (
            <div className="flex flex-wrap items-end gap-3">
              <div className="min-w-64 flex-1">
                <label className="mb-1 block text-sm font-medium text-text" htmlFor="portal-user">
                  People with SLLR access
                </label>
                <Select
                  id="portal-user"
                  className="w-full"
                  value={pickedUser}
                  options={[{ value: '', label: 'Select a person…' }, ...portalOptions]}
                  onChange={(e) => setPickedUser(e.target.value)}
                />
              </div>
              <Button
                type="button"
                variant="primary"
                disabled={!pickedUser}
                onClick={() => addEmailToCandidates(pickedUser)}
              >
                Add user
              </Button>
            </div>
          ) : null}
          <form onSubmit={handleAddTyped} className="flex flex-wrap items-end gap-3">
            <div className="min-w-64 flex-1">
              <label className="mb-1 block text-sm font-medium text-text" htmlFor="approver-email">
                {portalOptions.length > 0 ? 'Email not listed' : 'Portal email'}
              </label>
              <TextInput
                id="approver-email"
                type="email"
                value={typedEmail}
                onChange={(e) => setTypedEmail(e.target.value)}
                placeholder="user@powerlearn.us"
                className="w-full"
              />
            </div>
            <Button type="submit" variant={portalOptions.length > 0 ? 'default' : 'primary'} disabled={!typedEmail.trim()}>
              Add email
            </Button>
          </form>
        </div>
      </Card>

      <section>
        <h2 className="mb-1 text-lg font-medium text-text">Technical Blocks</h2>
        <p className="mb-4 text-sm text-muted">
          One card per block. Changing the dropdown replaces the approver(s) for that block.
        </p>
        {blocks.length === 0 ? (
          <Card>
            <p className="text-muted">
              No technical blocks are configured yet. Add them under Settings, then return here to
              assign approvers.
            </p>
          </Card>
        ) : (
          <div className="grid gap-4">
            {blocks.map((row) => {
              const primary = row.emails[0] ?? ''
              const extras = row.emails.slice(1)
              const busy = saving === row.technical_block
              const alsoOptions = selectOptions.filter((opt) => opt.value && !row.emails.includes(opt.value))
              return (
                <div
                  key={row.technical_block}
                  className="rounded-lg border border-line border-l-4 border-l-accent bg-panel p-6"
                >
                  <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
                    <h3 className="font-mono text-lg font-medium text-accent">{row.technical_block}</h3>
                    {row.emails.length === 0 ? (
                      <span className="text-[11px] uppercase tracking-wide text-muted">No approver</span>
                    ) : (
                      <span className="text-[11px] uppercase tracking-wide text-muted">
                        {row.emails.length === 1 ? '1 approver' : `${row.emails.length} approvers`}
                      </span>
                    )}
                  </div>
                  {extras.length > 0 ? (
                    <div className="mb-4 flex flex-wrap gap-2">
                      {row.emails.map((email) => (
                        <span
                          key={email}
                          className="inline-flex items-center gap-2 rounded-md border border-line bg-raised px-2 py-1 font-mono text-xs text-text"
                        >
                          {email}
                          <button
                            type="button"
                            className="text-muted hover:text-danger"
                            disabled={busy}
                            onClick={() => void handleRemoveEmail(row.technical_block, email)}
                            aria-label={`Remove ${email}`}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <label className="mb-1 block text-sm font-medium text-text">
                    Primary approver
                  </label>
                  <Select
                    className="w-full max-w-lg"
                    value={primary}
                    disabled={busy || candidates.length === 0}
                    options={
                      primary && !selectOptions.some((opt) => opt.value === primary)
                        ? [...selectOptions, { value: primary, label: primary }]
                        : selectOptions
                    }
                    onChange={(e) => handlePrimaryChange(row.technical_block, e.target.value)}
                  />
                  {candidates.length === 0 ? (
                    <p className="mt-2 text-sm text-muted">Add a user above to populate this list.</p>
                  ) : null}
                  {alsoOptions.length > 0 && primary ? (
                    <div className="mt-4 flex flex-wrap items-end gap-3">
                      <div className="min-w-64 flex-1">
                        <label className="mb-1 block text-sm font-medium text-text">
                          Also approve
                        </label>
                        <Select
                          className="w-full"
                          value={secondary[row.technical_block] || ''}
                          disabled={busy}
                          options={[{ value: '', label: 'Optional secondary…' }, ...alsoOptions]}
                          onChange={(e) =>
                            setSecondary((current) => ({
                              ...current,
                              [row.technical_block]: e.target.value,
                            }))
                          }
                        />
                      </div>
                      <Button
                        type="button"
                        variant="default"
                        disabled={busy || !secondary[row.technical_block]}
                        onClick={() => void handleAlsoApprove(row.technical_block)}
                      >
                        Add
                      </Button>
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
