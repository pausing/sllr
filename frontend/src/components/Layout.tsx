import { useEffect, useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router'
import { api, PortalMe } from '../lib/api'

const PORTAL_URL = 'https://portal.powerlearn.us/'

const NAV_ITEMS: { path: string; label: string; adminOnly?: boolean }[] = [
  { path: '/', label: 'Dashboard' },
  { path: '/lessons', label: 'Browse Lessons' },
  { path: '/lessons/new', label: 'Add Lesson' },
  { path: '/approve', label: 'Approve' },
  { path: '/approvers', label: 'Approvers', adminOnly: true },
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
    <div className="flex min-h-screen flex-col">
      <header className="flex h-11 shrink-0 items-center justify-between gap-4 border-b border-line bg-panel px-4">
        <div className="flex min-w-0 items-center gap-4">
          <div className="text-[11px] uppercase tracking-[0.18em] text-accent">
            Lessons Learned
          </div>
          <a
            href={PORTAL_URL}
            className="shrink-0 text-[11px] uppercase tracking-[0.18em] text-muted hover:text-text"
          >
            Portal
          </a>
        </div>
        {email ? (
          <p className="truncate text-[13px] text-muted">
            Hello, <span className="text-text">{email}</span>
            {me?.admin ? (
              <span className="ml-2 inline-block align-middle rounded border border-line px-1 py-px text-[9px] uppercase tracking-wide text-muted">
                admin
              </span>
            ) : null}
          </p>
        ) : null}
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="w-64 shrink-0 border-r border-line bg-panel">
          <nav className="p-4">
            <ul className="space-y-1">
              {NAV_ITEMS.filter((item) => !item.adminOnly || me?.admin).map((item) => {
                const isActive = isNavActive(location.pathname, item.path)

                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-accent-dim font-medium text-accent'
                          : 'text-muted hover:bg-raised hover:text-text'
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

        <main className="flex-1 overflow-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
