import { Routes, Route } from 'react-router'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Lessons } from './pages/Lessons'
import { LessonNew } from './pages/LessonNew'
import { LessonEdit } from './pages/LessonEdit'
import { Approve } from './pages/Approve'
import { Approvers } from './pages/Approvers'
import { Implementation } from './pages/Implementation'
import { Validation } from './pages/Validation'
import { Duplicates } from './pages/Duplicates'
import { Report } from './pages/Report'
import { Export } from './pages/Export'
import { Reports } from './pages/Reports'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="lessons" element={<Lessons />} />
        <Route path="lessons/new" element={<LessonNew />} />
        <Route path="lessons/:id" element={<LessonEdit />} />
        <Route path="approve" element={<Approve />} />
        <Route path="approvers" element={<Approvers />} />
        <Route path="implementation" element={<Implementation />} />
        <Route path="validation" element={<Validation />} />
        <Route path="duplicates" element={<Duplicates />} />
        <Route path="report" element={<Report />} />
        <Route path="export" element={<Export />} />
        <Route path="reports" element={<Reports />} />
      </Route>
    </Routes>
  )
}

export default App
