import type { Lesson } from './api'
import {
  BOARD_STAGE_LEGEND,
  filterWorkflowLessons,
  groupLessonsByBlock,
  lessonBlock,
  lessonBoardStage,
  UNASSIGNED_BLOCK,
} from './workflowBoard'

function sample(overrides: Partial<Lesson> = {}): Lesson {
  return {
    'Lesson ID': 'LL-001',
    Title: 'Cable tray clearance',
    'Technical Block': 'PV',
    'Project Phase': 'Construction',
    'Event Description': 'inverter trip on site',
    'Root Cause': 'undersized conductor',
    Impact: 'Schedule',
    'Lesson Learned': 'Check ratings early',
    Recommendation: 'Update RFQ template',
    Keywords: 'cable-tray',
    Status: 'Draft',
    'Implementation Status': 'Not Implemented',
    Owner: 'owner@powerlearn.us',
    ...overrides,
  }
}

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message)
}

export function runWorkflowBoardChecks(): void {
  assert(lessonBoardStage(sample()) === 'Draft', 'draft stage')
  assert(
    lessonBoardStage(sample({ Status: 'Approved' })) === 'Approved',
    'approved open stage',
  )
  assert(
    lessonBoardStage(sample({ Status: 'Approved', 'Implementation Status': 'Implemented' })) ===
      'Implemented',
    'implemented wins over approved',
  )
  assert(lessonBoardStage(sample({ Status: '', 'Implementation Status': '' })) === 'Draft', 'blank is draft')
  assert(lessonBlock(sample()) === 'PV', 'named block')
  assert(lessonBlock(sample({ 'Technical Block': '  ' })) === UNASSIGNED_BLOCK, 'blank block')

  const lessons = [
    sample({ 'Lesson ID': 'LL-001', 'Technical Block': 'PV', Status: 'Draft' }),
    sample({ 'Lesson ID': 'LL-002', 'Technical Block': 'BESS', Status: 'Approved', Title: 'BESS fire wall' }),
    sample({
      'Lesson ID': 'LL-003',
      'Technical Block': '',
      Status: 'Approved',
      'Implementation Status': 'Implemented',
      Title: 'Orphan closed',
    }),
    sample({ 'Lesson ID': 'LL-004', 'Technical Block': 'Mystery', Status: 'Draft' }),
  ]

  const filtered = filterWorkflowLessons(lessons, { status: 'Approved', q: 'bess' })
  assert(filtered.length === 1 && filtered[0]['Lesson ID'] === 'LL-002', 'status + search')
  assert(
    filterWorkflowLessons(lessons, { status: 'Approved' }).every((row) => lessonBoardStage(row) === 'Approved'),
    'approved filter excludes implemented',
  )
  assert(filterWorkflowLessons(lessons, { status: 'Implemented' }).length === 1, 'implemented filter')
  assert(filterWorkflowLessons(lessons, { technical_block: 'PV' }).length === 1, 'block filter')
  assert(filterWorkflowLessons(lessons, { phase: 'O&M' }).length === 0, 'phase miss')

  const lanes = groupLessonsByBlock(lessons, ['Civil', 'HV & Grid', 'PV', 'BESS'])
  assert(lanes.map((l) => l.block).join('|') === 'Civil|HV & Grid|PV|BESS|Mystery|Unassigned', 'lane order')
  assert(lanes.find((l) => l.block === 'Civil')?.lessons.length === 0, 'empty known lane')
  assert(lanes.find((l) => l.block === 'PV')?.lessons[0]['Lesson ID'] === 'LL-001', 'pv cards')
  assert(lanes.find((l) => l.block === UNASSIGNED_BLOCK)?.lessons.length === 1, 'unassigned lane')

  const one = groupLessonsByBlock(lessons, ['Civil', 'PV'], 'PV')
  assert(one.length === 1 && one[0].block === 'PV' && one[0].lessons.length === 1, 'selected block')

  assert(BOARD_STAGE_LEGEND.length === 3, 'legend covers stages')
  assert(BOARD_STAGE_LEGEND[1].color === '#3dcc8c', 'approved uses accent')
}

runWorkflowBoardChecks()
