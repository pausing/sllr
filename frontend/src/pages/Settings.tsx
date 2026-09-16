import { FormEvent, useEffect, useState } from 'react'
import { api, PortalMe, VocabItem, VocabKind } from '../lib/api'
import { Button, Card, TextInput } from '../components/ui'

const TABS: { id: VocabKind; label: string; singular: string; help: string }[] = [
  {
    id: 'categories',
    label: 'Categories',
    singular: 'category',
    help: 'Lesson Category values used on create/edit forms and validation.',
  },
  {
    id: 'technical_blocks',
    label: 'Technical Blocks',
    singular: 'technical block',
    help: 'Lesson Technical Block values. Approvers are assigned per block.',
  },
  {
    id: 'phases',
    label: 'Project Phases',
    singular: 'project phase',
    help: 'Lesson Project Phase values. Order is the order shown in dropdowns.',
  },
]

export function Settings() {
  const [me, setMe] = useState<PortalMe | null>(null)
  const [items, setItems] = useState<Record<VocabKind, VocabItem[]>>({
    categories: [],
    technical_blocks: [],
    phases: [],
  })
  const [tab, setTab] = useState<VocabKind>('categories')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [code, setCode] = useState('')
  const [label, setLabel] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [editCode, setEditCode] = useState('')
  const [editLabel, setEditLabel] = useState('')

  const load = async () => {
    const user = await api.getMe()
    setMe(user)
    if (user?.admin !== true) return
    setItems(await api.getVocab())
  }

  useEffect(() => {
    load()
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load settings'))
      .finally(() => setLoading(false))
  }, [])

  const isAdmin = me?.admin === true
  const current = items[tab]

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault()
    const nextCode = code.trim()
    if (!nextCode) return
    setSaving(true)
    setError(null)
    try {
      await api.createVocab(tab, nextCode, label.trim() || nextCode)
      setCode('')
      setLabel('')
      setItems(await api.getVocab())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add code')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (item: VocabItem) => {
    setEditing(item.code)
    setEditCode(item.code)
    setEditLabel(item.label)
  }

  const handleSaveEdit = async (original: string) => {
    setSaving(true)
    setError(null)
    try {
      await api.updateVocab(tab, original, {
        code: editCode.trim() || original,
        label: editLabel.trim() || editCode.trim() || original,
      })
      setEditing(null)
      setItems(await api.getVocab())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rename')
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (item: VocabItem) => {
    setSaving(true)
    setError(null)
    try {
      await api.updateVocab(tab, item.code, { active: !item.active })
      setItems(await api.getVocab())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (item: VocabItem) => {
    if (!window.confirm(`Delete ${item.code}? Forms will no longer offer this value.`)) return
    setSaving(true)
    setError(null)
    try {
      await api.deleteVocab(tab, item.code)
      setItems(await api.getVocab())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
    } finally {
      setSaving(false)
    }
  }

  const move = async (index: number, direction: -1 | 1) => {
    const next = index + direction
    if (next < 0 || next >= current.length) return
    const codes = current.map((item) => item.code)
    const [removed] = codes.splice(index, 1)
    codes.splice(next, 0, removed)
    setSaving(true)
    setError(null)
    try {
      const updated = await api.reorderVocab(tab, codes)
      setItems((prev) => ({ ...prev, [tab]: updated }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reorder')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="text-muted">Loading...</div>

  if (!isAdmin) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-text mb-2 md:text-3xl">Settings</h1>
        <p className="text-muted">Portal admin required to edit vocabulary presets.</p>
      </div>
    )
  }

  const tabMeta = TABS.find((item) => item.id === tab)!

  return (
    <div className="max-w-4xl">
      <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-accent">Administration</p>
      <h1 className="mb-2 text-2xl font-bold text-text md:text-3xl">Settings</h1>
      <p className="mb-8 max-w-2xl text-muted">
        Manage the controlled vocabulary used on lesson forms and validation. Changes are stored
        live (no image rebuild). Statuses stay as shipped defaults.
      </p>

      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}

      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => {
              setTab(item.id)
              setEditing(null)
            }}
            className={`min-h-11 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === item.id
                ? 'bg-accent-dim text-accent'
                : 'border border-line bg-panel text-muted hover:text-text'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <Card className="mb-6">
        <h2 className="mb-1 text-lg font-medium text-text">Add {tabMeta.singular}</h2>
        <p className="mb-4 text-sm text-muted">{tabMeta.help}</p>
        <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
          <div className="min-w-0 w-full flex-1 sm:min-w-40">
            <label className="mb-1 block text-sm font-medium text-text" htmlFor="vocab-code">
              Code
            </label>
            <TextInput
              id="vocab-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. HSE"
              className="w-full"
            />
          </div>
          <div className="min-w-0 w-full flex-1 sm:min-w-40">
            <label className="mb-1 block text-sm font-medium text-text" htmlFor="vocab-label">
              Label
            </label>
            <TextInput
              id="vocab-label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Display name (optional)"
              className="w-full"
            />
          </div>
          <Button type="submit" variant="primary" disabled={saving || !code.trim()}>
            Add
          </Button>
        </form>
      </Card>

      {current.length === 0 ? (
        <Card>
          <p className="text-muted">No values yet. Add a code above.</p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-line bg-panel">
          <table className="w-full min-w-[36rem] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-muted">
                {tab === 'phases' ? <th className="px-4 py-3 font-medium w-24">Order</th> : null}
                <th className="px-4 py-3 font-medium">Code</th>
                <th className="px-4 py-3 font-medium">Label</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {current.map((item, index) => (
                <tr key={item.code} className="border-b border-line last:border-0">
                  {tab === 'phases' ? (
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          className="px-2 py-1"
                          disabled={saving || index === 0}
                          onClick={() => void move(index, -1)}
                        >
                          ↑
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          className="px-2 py-1"
                          disabled={saving || index === current.length - 1}
                          onClick={() => void move(index, 1)}
                        >
                          ↓
                        </Button>
                      </div>
                    </td>
                  ) : null}
                  <td className="px-4 py-3 font-mono text-accent">
                    {editing === item.code ? (
                      <TextInput value={editCode} onChange={(e) => setEditCode(e.target.value)} />
                    ) : (
                      item.code
                    )}
                  </td>
                  <td className="px-4 py-3 text-text">
                    {editing === item.code ? (
                      <TextInput value={editLabel} onChange={(e) => setEditLabel(e.target.value)} />
                    ) : (
                      item.label
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted">{item.active ? 'Active' : 'Inactive'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap justify-end gap-2">
                      {editing === item.code ? (
                        <>
                          <Button type="button" variant="primary" disabled={saving} onClick={() => void handleSaveEdit(item.code)}>
                            Save
                          </Button>
                          <Button type="button" variant="ghost" onClick={() => setEditing(null)}>
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button type="button" variant="ghost" disabled={saving} onClick={() => startEdit(item)}>
                            Rename
                          </Button>
                          <Button type="button" variant="ghost" disabled={saving} onClick={() => void handleToggle(item)}>
                            {item.active ? 'Deactivate' : 'Activate'}
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            className="text-danger"
                            disabled={saving}
                            onClick={() => void handleDelete(item)}
                          >
                            Delete
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
