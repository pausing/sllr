import { canDeleteLesson, canEditLesson, emailsMatch, lessonPath, normalizeEmail } from './lessonAccess'

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message)
}

export function runLessonAccessChecks(): void {
  assert(normalizeEmail('  Owner@Powerlearn.us  ') === 'owner@powerlearn.us', 'normalize')
  assert(emailsMatch('  Owner@Powerlearn.us  ', 'owner@powerlearn.us'), 'owner match')
  assert(!emailsMatch('', ''), 'empty emails do not match')
  assert(canEditLesson({ admin: true, email: null }, 'other@powerlearn.us'), 'admin can edit')
  assert(canEditLesson({ admin: false, email: '  Owner@Powerlearn.us  ' }, 'owner@powerlearn.us'), 'owner can edit')
  assert(!canEditLesson({ admin: false, email: 'other@powerlearn.us' }, 'owner@powerlearn.us'), 'other cannot edit')
  assert(!canEditLesson(null, 'owner@powerlearn.us'), 'missing me cannot edit')
  assert(lessonPath('LL/1') === '/lessons/LL%2F1', 'encode id')
  assert(lessonPath('LL/1', true) === '/lessons/LL%2F1?edit=1', 'edit query')
  const draft = { Owner: 'owner@powerlearn.us', Status: 'Draft', 'Implementation Status': 'Not Implemented' }
  const approved = { ...draft, Status: 'Approved' }
  assert(canDeleteLesson({ admin: true, email: null }, approved), 'admin can delete approved')
  assert(canDeleteLesson({ admin: false, email: '  Owner@Powerlearn.us  ' }, draft), 'owner can delete draft')
  assert(!canDeleteLesson({ admin: false, email: 'owner@powerlearn.us' }, approved), 'owner cannot delete approved')
  assert(!canDeleteLesson({ admin: false, email: 'other@powerlearn.us' }, draft), 'non-owner cannot delete')
  assert(!canDeleteLesson(null, draft), 'missing me cannot delete')
}

runLessonAccessChecks()
