import type { Lesson } from './api'
import { lessonMatchesQuery } from './lessonSearch'

export const UNASSIGNED_BLOCK = 'Unassigned'

export type BoardStage = 'Draft' | 'Approved' | 'Implemented'

export const BOARD_STAGES: BoardStage[] = ['Draft', 'Approved', 'Implemented']

export const BOARD_STAGE_LEGEND: {
  stage: BoardStage
  token: string
  color: string
  meaning: string
}[] = [
  {
    stage: 'Draft',
    token: 'amber',
    color: '#e8a838',
    meaning: 'Captured, not yet approved',
  },
  {
    stage: 'Approved',
    token: 'accent',
    color: '#3dcc8c',
    meaning: 'Approved, still open for implementation',
  },
  {
    stage: 'Implemented',
    token: 'sky',
    color: '#6b9bff',
    meaning: 'Implemented / closed',
  },
]

export const BOARD_STAGE_CLASSES: Record<
  BoardStage,
  { border: string; glow: string; chip: string; pip: string; bar: string }
> = {
  Draft: {
    border: 'border-amber/70',
    glow: 'shadow-[0_0_0_1px_rgba(232,168,56,0.18)]',
    chip: 'border-amber/50 bg-amber/15 text-amber',
    pip: 'bg-amber',
    bar: 'bg-amber',
  },
  Approved: {
    border: 'border-accent/80',
    glow: 'shadow-[0_0_0_1px_rgba(61,204,140,0.22)]',
    chip: 'border-accent/50 bg-accent-dim text-accent',
    pip: 'bg-accent',
    bar: 'bg-accent',
  },
  Implemented: {
    border: 'border-sky/70',
    glow: 'shadow-[0_0_0_1px_rgba(107,155,255,0.2)]',
    chip: 'border-sky/50 bg-sky/15 text-sky',
    pip: 'bg-sky',
    bar: 'bg-sky',
  },
}

/** Workflow color is Implementation Status when closed, else lesson Status. */
export function lessonBoardStage(lesson: Pick<Lesson, 'Status' | 'Implementation Status'>): BoardStage {
  const impl = (lesson['Implementation Status'] ?? '').trim()
  if (impl === 'Implemented') return 'Implemented'
  const status = (lesson.Status ?? '').trim()
  if (status === 'Approved') return 'Approved'
  return 'Draft'
}

export function lessonBlock(lesson: Pick<Lesson, 'Technical Block'>): string {
  const block = (lesson['Technical Block'] ?? '').trim()
  return block || UNASSIGNED_BLOCK
}

export function filterWorkflowLessons(
  lessons: Lesson[],
  filters: {
    status?: string
    technical_block?: string
    phase?: string
    q?: string
  },
): Lesson[] {
  const status = filters.status?.trim() ?? ''
  const block = filters.technical_block?.trim() ?? ''
  const phase = filters.phase?.trim() ?? ''
  return lessons.filter((lesson) => {
    if (status && (lesson.Status ?? '').trim() !== status) return false
    if (block && lessonBlock(lesson) !== block) return false
    if (phase && (lesson['Project Phase'] ?? '').trim() !== phase) return false
    return lessonMatchesQuery(lesson, filters.q ?? '')
  })
}

export function groupLessonsByBlock(
  lessons: Lesson[],
  blockOrder: string[],
  selectedBlock = '',
): { block: string; lessons: Lesson[] }[] {
  const buckets = new Map<string, Lesson[]>()
  for (const block of blockOrder) {
    const key = block.trim()
    if (key) buckets.set(key, [])
  }
  for (const lesson of lessons) {
    const block = lessonBlock(lesson)
    const list = buckets.get(block)
    if (list) list.push(lesson)
    else buckets.set(block, [lesson])
  }

  const selected = selectedBlock.trim()
  if (selected) {
    return [{ block: selected, lessons: buckets.get(selected) ?? [] }]
  }

  const known = blockOrder.map((b) => b.trim()).filter(Boolean)
  const extras = [...buckets.keys()]
    .filter((key) => key !== UNASSIGNED_BLOCK && !known.includes(key))
    .sort((a, b) => a.localeCompare(b))
  const keys = [...known, ...extras]
  if ((buckets.get(UNASSIGNED_BLOCK) ?? []).length > 0) {
    keys.push(UNASSIGNED_BLOCK)
  }
  return keys.map((block) => ({ block, lessons: buckets.get(block) ?? [] }))
}
