import { canEditLesson, emailsMatch, lessonPath, normalizeEmail } from './lessonAccess'

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
}

runLessonAccessChecks()
