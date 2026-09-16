const API_BASE = '/sllr/api'

export interface Lesson {
  'Lesson ID': string
  Title: string
  Category: string
  'Technical Block': string
  'Sub-category': string
  'Project Phase': string
  'Root Cause': string
  'What Happened': string
  Impact: string
  'Lesson Learned': string
  Recommendation: string
  'Recommendation Due Date'?: string
  Keywords?: string
  Status: string
  'Implementation Status': string
  Owner: string
  'Created Date'?: string
  'Modified Date'?: string
}

export interface References {
  categories: string[]
  technical_blocks: string[]
  phases: string[]
  statuses: string[]
  implementation_statuses: string[]
}

export interface PortalMe {
  id?: string | null
  user_id: string | null
  email: string | null
  admin: boolean | null
}

export interface Approver {
  email: string
  technical_blocks: string[]
}

export interface ApproverBlock {
  technical_block: string
  emails: string[]
}

export interface ApproversPayload {
  approvers: Approver[]
  blocks: ApproverBlock[]
}

export interface MyApproverRules {
  email: string | null
  admin: boolean
  technical_blocks: string[]
}

export interface VocabItem {
  kind: string
  code: string
  label: string
  sort_order: number
  active: boolean
}

export type VocabKind = 'categories' | 'technical_blocks' | 'phases'

export interface SllrUser {
  email: string
  name?: string | null
}

export interface KPIs {
  total_lessons: number
  repeated_issues_count: number
  capture_to_approval_days_avg: number | null
  approved_count: number
  implemented_count: number
  pct_implemented: number
  overdue_not_implemented_count: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  by_technical_block: Record<string, number>
  by_implementation_status: Record<string, number>
}

export const api = {
  async getMe(): Promise<PortalMe> {
    const res = await fetch(`${API_BASE}/me`)
    if (!res.ok) throw new Error('Failed to fetch current user')
    const data = await res.json()
    if (data == null || typeof data !== 'object') {
      throw new Error('Failed to fetch current user')
    }
    const user = data as Partial<PortalMe> & { id?: string | null }
    return {
      id: user.id ?? user.user_id ?? null,
      user_id: user.user_id ?? user.id ?? null,
      email: user.email ?? null,
      admin: user.admin ?? null,
    }
  },

  async getReferences(): Promise<References> {
    const res = await fetch(`${API_BASE}/references`)
    if (!res.ok) throw new Error('Failed to fetch references')
    return res.json()
  },

  async getLessons(filters?: {
    technical_block?: string
    phase?: string
    status?: string
    implementation_status?: string
    category?: string
  }): Promise<Lesson[]> {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value)
      })
    }
    const res = await fetch(`${API_BASE}/lessons?${params}`)
    if (!res.ok) throw new Error('Failed to fetch lessons')
    return res.json()
  },

  async getLesson(id: string): Promise<Lesson> {
    const res = await fetch(`${API_BASE}/lessons/${encodeURIComponent(id)}`)
    if (!res.ok) throw new Error('Failed to fetch lesson')
    return res.json()
  },

  async getNextId(): Promise<{ suggested_id: string }> {
    const res = await fetch(`${API_BASE}/lessons/next-id`)
    if (!res.ok) throw new Error('Failed to get next ID')
    return res.json()
  },

  async createLesson(lesson: Partial<Lesson>): Promise<Lesson> {
    const res = await fetch(`${API_BASE}/lessons`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lesson),
    })
    if (!res.ok) {
      throw new Error(await readApiError(res, 'Failed to create lesson'))
    }
    return res.json()
  },

  async updateLesson(id: string, lesson: Partial<Lesson>): Promise<Lesson> {
    const res = await fetch(`${API_BASE}/lessons/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lesson),
    })
    if (!res.ok) {
      throw new Error(await readApiError(res, 'Failed to update lesson'))
    }
    return res.json()
  },

  async patchLesson(id: string, patch: Partial<Lesson>): Promise<Lesson> {
    const res = await fetch(`${API_BASE}/lessons/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    })
    if (!res.ok) {
      throw new Error(await readApiError(res, 'Failed to patch lesson'))
    }
    return res.json()
  },

  async getKPIs(): Promise<KPIs> {
    const res = await fetch(`${API_BASE}/kpis`)
    if (!res.ok) throw new Error('Failed to fetch KPIs')
    return res.json()
  },

  async getValidationReport(): Promise<string> {
    const res = await fetch(`${API_BASE}/reports/validation`)
    if (!res.ok) throw new Error('Failed to fetch validation report')
    return res.text()
  },

  async getDuplicatesReport(): Promise<string> {
    const res = await fetch(`${API_BASE}/reports/duplicates`)
    if (!res.ok) throw new Error('Failed to fetch duplicates report')
    return res.text()
  },

  async getKPIReport(): Promise<string> {
    const res = await fetch(`${API_BASE}/reports/kpi`)
    if (!res.ok) throw new Error('Failed to fetch KPI report')
    return res.text()
  },

  async downloadDashboardCSV(): Promise<void> {
    const res = await fetch(`${API_BASE}/reports/dashboard-export`)
    if (!res.ok) throw new Error('Failed to download dashboard CSV')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'dashboard_export.csv'
    a.click()
    URL.revokeObjectURL(url)
  },

  async downloadPDF(): Promise<void> {
    const res = await fetch(`${API_BASE}/export/pdf`, { method: 'POST' })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Failed to generate PDF')
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'lessons_learned.pdf'
    a.click()
    URL.revokeObjectURL(url)
  },

  async downloadHTML(): Promise<void> {
    const res = await fetch(`${API_BASE}/export/html`, { method: 'POST' })
    if (!res.ok) throw new Error('Failed to generate HTML')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'lessons_learned.html'
    a.click()
    URL.revokeObjectURL(url)
  },

  async getApprovers(): Promise<ApproversPayload> {
    const res = await fetch(`${API_BASE}/approvers`)
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to fetch approvers'))
    const data = await res.json()
    return {
      approvers: Array.isArray(data?.approvers) ? data.approvers : [],
      blocks: Array.isArray(data?.blocks) ? data.blocks : [],
    }
  },

  async getMyApproverRules(): Promise<MyApproverRules> {
    const res = await fetch(`${API_BASE}/approvers/me`)
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to fetch approver rules'))
    const data = await res.json()
    return {
      email: data?.email ?? null,
      admin: data?.admin === true,
      technical_blocks: Array.isArray(data?.technical_blocks) ? data.technical_blocks : [],
    }
  },

  async setApproverBlocks(email: string, technical_blocks: string[]): Promise<Approver> {
    const res = await fetch(`${API_BASE}/approvers`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, technical_blocks }),
    })
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to save approver'))
    return res.json()
  },

  async setBlockApprovers(technical_block: string, emails: string[]): Promise<ApproverBlock> {
    const res = await fetch(`${API_BASE}/approvers/block`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ technical_block, emails }),
    })
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to save block approver'))
    return res.json()
  },

  async addBlockApprover(technical_block: string, email: string): Promise<ApproverBlock> {
    const res = await fetch(`${API_BASE}/approvers/block`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ technical_block, email }),
    })
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to add secondary approver'))
    return res.json()
  },

  async deleteApprover(email: string): Promise<void> {
    const res = await fetch(`${API_BASE}/approvers/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to remove approver'))
  },

  async deleteApproverBlock(email: string, technical_block: string): Promise<void> {
    const res = await fetch(
      `${API_BASE}/approvers/${encodeURIComponent(email)}/${encodeURIComponent(technical_block)}`,
      { method: 'DELETE' },
    )
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to remove approver mapping'))
  },

  async getPortalSllrUsers(): Promise<{ users: SllrUser[]; available: boolean }> {
    try {
      const res = await fetch('https://portal.powerlearn.us/api/sllr-users', {
        credentials: 'include',
      })
      if (!res.ok) return { users: [], available: false }
      const data = await res.json()
      return { users: parseSllrUsers(data), available: true }
    } catch {
      return { users: [], available: false }
    }
  },

  async getVocab(): Promise<Record<VocabKind, VocabItem[]>> {
    const res = await fetch(`${API_BASE}/settings/vocab`)
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to fetch settings'))
    const data = await res.json()
    return {
      categories: Array.isArray(data?.categories) ? data.categories : [],
      technical_blocks: Array.isArray(data?.technical_blocks) ? data.technical_blocks : [],
      phases: Array.isArray(data?.phases) ? data.phases : [],
    }
  },

  async createVocab(kind: VocabKind, code: string, label?: string): Promise<VocabItem> {
    const res = await fetch(`${API_BASE}/settings/vocab/${encodeURIComponent(kind)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, label: label || code }),
    })
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to add code'))
    return res.json()
  },

  async updateVocab(
    kind: VocabKind,
    code: string,
    patch: { code?: string; label?: string; active?: boolean; sort_order?: number },
  ): Promise<VocabItem> {
    const res = await fetch(
      `${API_BASE}/settings/vocab/${encodeURIComponent(kind)}/${encodeURIComponent(code)}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      },
    )
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to update code'))
    return res.json()
  },

  async deleteVocab(kind: VocabKind, code: string): Promise<void> {
    const res = await fetch(
      `${API_BASE}/settings/vocab/${encodeURIComponent(kind)}/${encodeURIComponent(code)}`,
      { method: 'DELETE' },
    )
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to delete code'))
  },

  async reorderVocab(kind: VocabKind, codes: string[]): Promise<VocabItem[]> {
    const res = await fetch(`${API_BASE}/settings/vocab/${encodeURIComponent(kind)}/order`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codes }),
    })
    if (!res.ok) throw new Error(await readApiError(res, 'Failed to reorder'))
    const data = await res.json()
    return Array.isArray(data?.items) ? data.items : []
  },
}

function formatDetail(detail: unknown): string | null {
  if (detail == null) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg)
        }
        return JSON.stringify(item)
      })
      .join(', ')
  }
  if (typeof detail === 'object' && Array.isArray((detail as { errors?: unknown }).errors)) {
    return ((detail as { errors: unknown[] }).errors).map(String).join(', ')
  }
  return null
}

async function readApiError(res: Response, fallback: string): Promise<string> {
  try {
    const err = await res.json()
    return formatDetail(err?.detail) || fallback
  } catch {
    return fallback
  }
}

function parseSllrUsers(data: unknown): SllrUser[] {
  const rows: unknown[] = Array.isArray(data)
    ? data
    : data && typeof data === 'object'
      ? Array.isArray((data as { users?: unknown }).users)
        ? (data as { users: unknown[] }).users
        : Array.isArray((data as { emails?: unknown }).emails)
          ? (data as { emails: unknown[] }).emails
          : []
      : []
  const users: SllrUser[] = []
  const seen = new Set<string>()
  for (const row of rows) {
    let email = ''
    let name: string | null = null
    if (typeof row === 'string') {
      email = row.trim().toLowerCase()
    } else if (row && typeof row === 'object') {
      const rec = row as { email?: unknown; name?: unknown; display_name?: unknown }
      email = typeof rec.email === 'string' ? rec.email.trim().toLowerCase() : ''
      const rawName = rec.name ?? rec.display_name
      name = typeof rawName === 'string' && rawName.trim() ? rawName.trim() : null
    }
    if (!email || !email.includes('@') || seen.has(email)) continue
    seen.add(email)
    users.push({ email, name })
  }
  return users
}
