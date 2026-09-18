import { useEffect, useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router'
import { api, PortalMe } from '../lib/api'

const PORTAL_URL = 'https://portal.powerlearn.us/'

const NAV_ITEMS: { path: string; label: string; adminOnly?: boolean }[] = [
  { path: '/', label: 'Dashboard' },
  { path: '/lessons', label: 'Browse Lessons' },
  { path: '/workflow', label: 'Workflow' },
  { path: '/lessons/new', label: 'Add Lesson' },
  { path: '/approve', label: 'Approve' },
  { path: '/approvers', label: 'Approvers', adminOnly: true },
  { path: '/settings', label: 'Settings', adminOnly: true },
  { path: '/activity', label: 'Activity', adminOnly: true },
  { path: '/implementation', label: 'Implementation' },
  { path: '/report', label: 'View Report' },
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

function NavLinks({
  pathname,
  isAdmin,
  onNavigate,
}: {
  pathname: string
  isAdmin: boolean
  onNavigate?: () => void
}) {
  return (
    <nav className="p-4">
      <ul className="space-y-1">
        {NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).map((item) => {
          const isActive = isNavActive(pathname, item.path)

          return (
            <li key={item.path}>
              <Link
                to={item.path}
                onClick={onNavigate}
                className={`flex min-h-11 items-center rounded-md px-3 py-2 text-sm transition-colors md:min-h-0 ${
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
  )
}

export function Layout() {
  const location = useLocation()
  const [me, setMe] = useState<PortalMe | null>(null)
  const [navOpen, setNavOpen] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)

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

  useEffect(() => {
    let cancelled = false
    const loadPending = () => {
      api
        .getPendingApprovalCount()
        .then((count) => {
          if (!cancelled) setPendingCount(count > 0 ? count : 0)
        })
        .catch(() => {
          if (!cancelled) setPendingCount(0)
        })
    }
    loadPending()
    const onFocus = () => loadPending()
    const onVisibility = () => {
      if (document.visibilityState === 'visible') loadPending()
    }
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      cancelled = true
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [location.pathname])

  useEffect(() => {
    setNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!navOpen) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setNavOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener('keydown', onKey)
    }
  }, [navOpen])

  const email = me?.email?.trim() ?? ''
  const isAdmin = me?.admin === true

  return (
    <div className="flex min-h-screen flex-col">
      <header className="relative z-50 flex h-11 shrink-0 items-center justify-between gap-2 border-b border-line bg-panel px-3 md:gap-4 md:px-4">
        <div className="flex min-w-0 items-center gap-2 md:gap-4">
          <button
            type="button"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-md text-text hover:bg-raised md:hidden"
            aria-label={navOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={navOpen}
            onClick={() => setNavOpen((open) => !open)}
          >
            {navOpen ? (
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            )}
          </button>
          <div className="truncate text-[11px] uppercase tracking-[0.18em] text-accent">
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
          <div className="flex min-w-0 max-w-[70%] items-center justify-end gap-2 md:max-w-[50%]">
            <p className="min-w-0 truncate text-right text-[13px] text-muted">
              Hello, <span className="text-text">{email}</span>
              {isAdmin ? (
                <span className="ml-2 inline-block align-middle rounded border border-line px-1 py-px text-[9px] uppercase tracking-wide text-muted">
                  admin
                </span>
              ) : null}
            </p>
            {pendingCount > 0 ? (
              <Link
                to="/approve"
                className="inline-flex shrink-0 items-center rounded-full border border-accent/50 bg-accent-dim px-2 py-0.5 text-[11px] font-medium text-accent hover:bg-accent/15"
                title="Open Approve"
              >
                {pendingCount === 1 ? '1 to approve' : `${pendingCount} to approve`}
              </Link>
            ) : null}
          </div>
        ) : null}
      </header>

      <div className="flex min-h-0 flex-1">
        {navOpen ? (
          <button
            type="button"
            className="fixed inset-x-0 bottom-0 top-11 z-40 border-0 bg-[#0c0e12]/70 p-0 md:hidden"
            aria-label="Close menu"
            onClick={() => setNavOpen(false)}
          />
        ) : null}

        <aside
          className={`fixed bottom-0 left-0 top-11 z-40 w-64 border-r border-line bg-panel transition-transform duration-200 md:hidden ${
            navOpen ? 'translate-x-0' : 'pointer-events-none -translate-x-full'
          }`}
          aria-hidden={!navOpen}
        >
          <NavLinks
            pathname={location.pathname}
            isAdmin={isAdmin}
            onNavigate={() => setNavOpen(false)}
          />
        </aside>

        <aside className="hidden w-64 shrink-0 border-r border-line bg-panel md:block">
          <NavLinks pathname={location.pathname} isAdmin={isAdmin} />
        </aside>

        <main className="min-w-0 flex-1 overflow-auto p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
