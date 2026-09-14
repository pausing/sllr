import { useEffect, useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router'
import { api, PortalMe } from '../lib/api'

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

function normalizePath(pathname: string): string {
  if (pathname !== '/' && pathname.endsWith('/')) {
    return pathname.replace(/\/+$/, '')
  }
  return pathname
}

/** Longest nav prefix wins. `/` is exact. `/lessons/:id` highlights Browse. */
function isNavActive(pathname: string, itemPath: string): boolean {
  const path = normalizePath(pathname)
  if (itemPath === '/') {
    return path === '/'
  }
  const matches = NAV_ITEMS.filter((item) => {
    if (item.path === '/') return false
    return path === item.path || path.startsWith(`${item.path}/`)
  })
  const winner = matches.sort((a, b) => b.path.length - a.path.length)[0]
  return winner?.path === itemPath
}

export function Layout() {
  const location = useLocation()
  const [me, setMe] = useState<PortalMe | null>(null)

  useEffect(() => {
    let cancelled = false
    api
      .getMe()
      .then((user) => {
        if (cancelled) return
        if (user?.email) setMe(user)
      })
      .catch(() => {
        /* ForwardAuth missing or /me failed — keep chrome intact */
      })
    return () => {
      cancelled = true
    }
  }, [])

  const email = me?.email?.trim() ?? ''

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-panel border-r border-line">
        <div className="p-6 border-b border-line">
          <h1 className="text-xl font-bold text-text">📋 SLLR</h1>
          <p className="text-sm text-muted mt-1">Lessons Learned Registry</p>
          {email ? (
            <p className="mt-3 text-sm text-muted break-all" title={email}>
              Hola, {email}
              {me?.admin ? (
                <span className="ml-2 inline-block align-middle rounded border border-line px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted">
                  admin
                </span>
              ) : null}
            </p>
          ) : null}
        </div>
        <nav className="p-4">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive = isNavActive(location.pathname, item.path)

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
