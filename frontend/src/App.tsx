import { Routes, Route } from 'react-router'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Lessons } from './pages/Lessons'
import { LessonNew } from './pages/LessonNew'
import { LessonEdit } from './pages/LessonEdit'
import { Approve } from './pages/Approve'
import { Approvers } from './pages/Approvers'
import { Settings } from './pages/Settings'
import { Activity } from './pages/Activity'
import { Implementation } from './pages/Implementation'
import { Report } from './pages/Report'

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
        <Route path="settings" element={<Settings />} />
        <Route path="activity" element={<Activity />} />
        <Route path="implementation" element={<Implementation />} />
        <Route path="report" element={<Report />} />
      </Route>
    </Routes>
  )
}

export default App
