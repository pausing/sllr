import type { Lesson } from './api'
import { lessonMatchesQuery } from './lessonSearch'

function sample(): Lesson {
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
  }
}

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message)
}

export function runLessonSearchChecks(): void {
  const lesson = sample()
  assert(lessonMatchesQuery(lesson, 'inverter trip'), 'event description')
  assert(lessonMatchesQuery(lesson, 'undersized'), 'root cause')
  assert(lessonMatchesQuery(lesson, 'cable-tray'), 'keywords')
  assert(lessonMatchesQuery(lesson, 'LL-001'), 'id')
  assert(!lessonMatchesQuery(lesson, 'zzzz'), 'no match')
}

runLessonSearchChecks()
