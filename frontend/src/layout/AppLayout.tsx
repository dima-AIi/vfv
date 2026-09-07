import { useEffect, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, NavLink, Outlet, matchPath, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../shared/api'
import { clearTokens, getAccessToken } from '../shared/auth'
import type { BreadcrumbItem } from '../shared/breadcrumbs'
import { breadcrumbFromPath } from '../shared/breadcrumbs'
import type {
  CustomerOut,
  Envelope,
  MeOut,
  NotificationOut,
  OrganizationOut,
  SearchResults,
} from '../shared/types'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../shared/ui'
import { ROLE_LABELS, formatLabel } from '../shared/labels'
import type { Project } from '../shared/types'

function SidebarLink({ to, icon, label }: { to: string; icon: string; label: string }) {
  return (
    <NavLink to={to} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
      <span className="sidebar-icon">{icon}</span>
      <span className="label">{label}</span>
    </NavLink>
  )
}

interface SearchHit {
  type: string
  id: string
  title: string
  to?: string
}

function GlobalSearch() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(query.trim()), 300)
    return () => clearTimeout(timer)
  }, [query])

  const active = debounced.length >= 2

  const searchQuery = useQuery<SearchResults>({
    queryKey: ['search', debounced],
    queryFn: async () =>
      (await api.get<Envelope<SearchResults>>('/search', { params: { q: debounced } })).data.data,
    enabled: active,
  })

  const hits: SearchHit[] = []
  const results = searchQuery.data
  if (results) {
    for (const p of results.projects) {
      hits.push({ type: 'Проект', id: p.id, title: p.name, to: `/projects/${p.id}` })
    }
    for (const t of results.tasks) {
      hits.push({
        type: 'Задача',
        id: t.id,
        title: t.title,
        to: `/projects/${t.project_id}?tab=tasks`,
      })
    }
    for (const d of results.documents) {
      hits.push({
        type: 'Документ',
        id: d.id,
        title: d.title,
        to: d.project_id ? `/projects/${d.project_id}?tab=documents` : undefined,
      })
    }
    for (const f of results.files) {
      hits.push({ type: 'Файл', id: f.id, title: f.filename })
    }
    for (const cust of results.customers) {
      hits.push({ type: 'Клиент', id: cust.id, title: cust.name, to: `/crm/${cust.id}` })
    }
  }

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') setOpen(false)
  }

  const go = (hit: SearchHit) => {
    setOpen(false)
    setQuery('')
    setDebounced('')
    if (hit.to) navigate(hit.to)
  }

  return (
    <div style={{ position: 'relative', flex: '0 1 360px', minWidth: 200 }}>
      <input
        className="input"
        type="search"
        placeholder="Глобальный поиск…"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        aria-label="Глобальный поиск"
      />
      {open && active && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 20 }} />
          <div
            className="card"
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: '110%',
              zIndex: 21,
              maxHeight: 420,
              overflowY: 'auto',
            }}
          >
            {searchQuery.isFetching && <Spinner />}
            {searchQuery.isError && (
              <div className="card-pad">
                <ErrorBanner error={searchQuery.error} />
              </div>
            )}
            {!searchQuery.isFetching && !searchQuery.isError && hits.length === 0 && (
              <EmptyState title="Ничего не найдено" hint="Уточните поисковый запрос." />
            )}
            {hits.map((hit) => (
              <button
                key={`${hit.type}-${hit.id}`}
                type="button"
                className="list-row list-row-button"
                onClick={() => go(hit)}
              >
                <div className="list-main">
                  <span className="list-title">{hit.title}</span>
                </div>
                <Badge tone="neutral">{hit.type}</Badge>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function NotificationsBell() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const unreadQuery = useQuery<number>({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const body = (
        await api.get<Envelope<NotificationOut[]>>('/notifications', {
          params: { unread: true, pageSize: 1 },
        })
      ).data
      return body.meta.pagination?.totalItems ?? 0
    },
    refetchInterval: 15000,
    enabled: Boolean(getAccessToken()),
  })

  const recentQuery = useQuery<NotificationOut[]>({
    queryKey: ['notifications', 'recent'],
    queryFn: async () =>
      (
        await api.get<Envelope<NotificationOut[]>>('/notifications', {
          params: { pageSize: 5 },
        })
      ).data.data,
    enabled: open,
  })

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => api.post(`/notifications/${id}/read`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const unread = unreadQuery.data ?? 0
  const recent = recentQuery.data ?? []

  return (
    <div style={{ position: 'relative' }}>
      <button
        className="btn btn-ghost"
        onClick={() => setOpen((value) => !value)}
        aria-label="Уведомления"
      >
        🔔{unread > 0 && <Badge tone="danger">{unread}</Badge>}
      </button>
      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 20 }} />
          <div
            className="card"
            style={{
              position: 'absolute',
              right: 0,
              top: '110%',
              width: 340,
              zIndex: 21,
              overflow: 'hidden',
            }}
          >
            <div className="card-pad" style={{ paddingBottom: 6 }}>
              <h2 className="card-title" style={{ margin: 0 }}>
                Уведомления
              </h2>
            </div>
            {recentQuery.isPending && <Spinner />}
            {recentQuery.isError && (
              <div className="card-pad">
                <ErrorBanner error={recentQuery.error} />
              </div>
            )}
            {!recentQuery.isPending && !recentQuery.isError && recent.length === 0 && (
              <div className="card-pad">
                <span className="muted">Новых уведомлений нет.</span>
              </div>
            )}
            {recent.map((notification) => (
              <button
                key={notification.id}
                type="button"
                className="list-row list-row-button"
                onClick={() => {
                  if (notification.read_at === null) markReadMutation.mutate(notification.id)
                  setOpen(false)
                  navigate('/notifications')
                }}
              >
                <div className="list-main">
                  <span
                    className="list-title"
                    style={{ fontWeight: notification.read_at === null ? 700 : 500 }}
                  >
                    {notification.title}
                  </span>
                  <div className="list-desc">{notification.body}</div>
                </div>
              </button>
            ))}
            <div className="card-pad" style={{ paddingTop: 8 }}>
              <button
                className="btn btn-ghost"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => {
                  setOpen(false)
                  navigate('/notifications')
                }}
              >
                Все уведомления
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function useBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const queryClient = useQueryClient()
  const workspaceMatch = matchPath('/projects/:projectId', pathname)
  const projectId = workspaceMatch?.params.projectId
  const project = projectId ? queryClient.getQueryData<Project>(['project', projectId]) : undefined
  const crmMatch = matchPath('/crm/:customerId', pathname)
  const customerId = crmMatch?.params.customerId
  const customer = customerId
    ? queryClient.getQueryData<CustomerOut>(['customer', customerId])
    : undefined
  return breadcrumbFromPath(pathname, project?.name ?? 'Проект', customer?.name)
}

function UserBlock() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [organizationName, setOrganizationName] = useState('')

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
    enabled: Boolean(getAccessToken()),
  })

  const createOrgMutation = useMutation({
    mutationFn: async (name: string) =>
      (await api.post<Envelope<OrganizationOut>>('/organizations', { name })).data.data,
    onSuccess: () => {
      setOrganizationName('')
      void queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })

  const logout = () => {
    void api
      .post('/auth/logout')
      .catch(() => undefined)
      .then(() => undefined as void)
      .finally(() => {
        clearTokens()
        queryClient.clear()
        navigate('/login', { replace: true })
      })
  }

  const onCreateOrg = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!organizationName.trim() || createOrgMutation.isPending) return
    createOrgMutation.mutate(organizationName.trim())
  }

  if (!getAccessToken() || meQuery.isError) return null

  return (
    <div className="topbar-actions" style={{ alignItems: 'flex-start' }}>
      {createOrgMutation.isError && (
        <div style={{ maxWidth: 320 }}>
          <ErrorBanner error={createOrgMutation.error} />
        </div>
      )}
      {meQuery.data && (
        <>
          <form onSubmit={onCreateOrg} className="topbar-actions" style={{ alignItems: 'center' }}>
            {meQuery.data.organization === null && (
              <>
                <input
                  className="input"
                  style={{ width: 220 }}
                  placeholder="Название организации"
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  maxLength={200}
                  aria-label="Название организации"
                />
                <button
                  className="btn btn-primary"
                  type="submit"
                  disabled={!organizationName.trim() || createOrgMutation.isPending}
                >
                  Создать организацию
                </button>
              </>
            )}
          </form>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: 600 }}>{meQuery.data.display_name}</div>
            <div className="muted">{meQuery.data.organization?.name ?? 'без организации'}</div>
            <div style={{ marginTop: 4, display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
              {meQuery.data.roles.map((role) => (
                <Badge key={role} tone="accent">
                  {formatLabel(ROLE_LABELS, role)}
                </Badge>
              ))}
            </div>
          </div>
          <button className="btn btn-ghost" onClick={logout} disabled={false}>
            Выйти
          </button>
        </>
      )}
      {meQuery.isLoading && <span className="muted">Загрузка профиля…</span>}
    </div>
  )
}

export default function AppLayout({ title }: { title: string }) {
  const location = useLocation()
  const items = useBreadcrumbs(location.pathname)

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
    enabled: Boolean(getAccessToken()),
  })
  const roles = meQuery.data?.roles ?? []
  const isOrgAdmin = roles.includes('org_admin') || roles.includes('platform_admin')

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">D</div>
          <div className="sidebar-brand-text">
            <div className="sidebar-brand-name">DevOS</div>
            <div className="sidebar-brand-sub">MVP-прототип</div>
          </div>
        </div>

        <div className="sidebar-section">Рабочее пространство</div>
        <nav className="sidebar-nav">
          <SidebarLink to="/" icon="◧" label="Панель" />
          <SidebarLink to="/projects" icon="▦" label="Проекты" />
          <SidebarLink to="/crm" icon="◈" label="CRM" />
          <SidebarLink to="/ai" icon="✦" label="AI-ассистент" />
        </nav>

        <div className="sidebar-section">Платформа</div>
        <nav className="sidebar-nav">
          {isOrgAdmin && <SidebarLink to="/users" icon="◉" label="Пользователи" />}
          {isOrgAdmin && <SidebarLink to="/audit" icon="❑" label="Аудит" />}
          <a className="sidebar-link" href="/api/v1/health" target="_blank" rel="noreferrer">
            <span className="sidebar-icon">◉</span>
            <span className="label">Проверка API</span>
          </a>
          <a className="sidebar-link" href="/docs" target="_blank" rel="noreferrer">
            <span className="sidebar-icon">❑</span>
            <span className="label">Документация API</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <SidebarLink to="/settings" icon="⚙" label="Настройки" />
          <div style={{ marginTop: 10 }}>
            Локальный прототип · провайдер <strong>mock</strong>
          </div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div>
            <div className="topbar-title">{title}</div>
            <div className="topbar-sub">
              Документационно-ориентированная AI-платформа управления бизнесом
            </div>
          </div>
          <GlobalSearch />
          <div className="topbar-actions" style={{ alignItems: 'center' }}>
            <NotificationsBell />
            <UserBlock />
          </div>
        </header>
        <main className="content">
          {items.length > 0 && (
            <nav className="breadcrumbs" aria-label="Хлебные крошки">
              {items.map((item: BreadcrumbItem, index) => {
                const isLast = index === items.length - 1
                const separator =
                  index > 0 ? (
                    <span key={`sep-${index}`} className="sep">
                      ›
                    </span>
                  ) : null
                return (
                  <span key={item.to} style={{ display: 'inline-flex', gap: 6 }}>
                    {separator}
                    {isLast || !item.label ? (
                      <span className="current">{item.label}</span>
                    ) : (
                      <Link to={item.to}>{item.label}</Link>
                    )}
                  </span>
                )
              })}
            </nav>
          )}
          <Outlet />
        </main>
      </div>
    </div>
  )
}
