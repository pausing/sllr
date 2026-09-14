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
  user_id: string | null
  email: string | null
  admin: boolean | null
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
    return res.json()
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
      const err = await res.json()
      throw new Error(err.detail?.errors?.join(', ') || err.detail || 'Failed to create lesson')
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
      const err = await res.json()
      throw new Error(err.detail?.errors?.join(', ') || err.detail || 'Failed to update lesson')
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
      const err = await res.json()
      throw new Error(err.detail?.errors?.join(', ') || err.detail || 'Failed to patch lesson')
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
}
