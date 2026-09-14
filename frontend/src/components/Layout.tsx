import { Outlet, Link, useLocation } from 'react-router'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard' },
  { path: '/lessons', label: 'Browse Lessons' },
  { path: '/lessons/new', label: 'Add Lesson' },
  { path: '/approve', label: 'Approve' },
  { path: '/implementation', label: 'Implementation' },
  { path: '/validation', label: 'Validation' },
  { path: '/duplicates', label: 'Duplicates' },
  { path: '/report', label: 'View Report' },
  { path: '/export', label: 'Export' },
  { path: '/reports', label: 'Reports' },
]

export function Layout() {
  const location = useLocation()
  
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-panel border-r border-line">
        <div className="p-6 border-b border-line">
          <h1 className="text-xl font-bold text-text">📋 SLLR</h1>
          <p className="text-sm text-muted mt-1">Lessons Learned Registry</p>
        </div>
        <nav className="p-4">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive = item.path === '/' 
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path) && item.path !== '/'
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`block px-3 py-2 rounded-md text-sm transition-colors ${
                      isActive
                        ? 'bg-accent-dim text-accent font-medium'
                        : 'text-muted hover:text-text hover:bg-raised'
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
