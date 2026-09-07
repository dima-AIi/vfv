export interface BreadcrumbItem {
  to: string
  label: string
}

const DASHBOARD: BreadcrumbItem = { to: '/', label: 'Панель' }
const PROJECTS: BreadcrumbItem = { to: '/projects', label: 'Проекты' }
const AI_WORKSPACE: BreadcrumbItem = { to: '/ai', label: 'AI-ассистент' }
const NOTIFICATIONS: BreadcrumbItem = { to: '/notifications', label: 'Уведомления' }
const CRM: BreadcrumbItem = { to: '/crm', label: 'CRM' }
const SETTINGS: BreadcrumbItem = { to: '/settings', label: 'Настройки' }
const USERS: BreadcrumbItem = { to: '/users', label: 'Пользователи' }
const AUDIT: BreadcrumbItem = { to: '/audit', label: 'Аудит' }

export function breadcrumbFromPath(
  pathname: string,
  projectLabel?: string,
  customerLabel?: string,
): BreadcrumbItem[] {
  if (pathname === '/') return [DASHBOARD]
  if (pathname === '/ai') return [DASHBOARD, AI_WORKSPACE]
  if (pathname === '/notifications') return [DASHBOARD, NOTIFICATIONS]
  if (pathname === '/crm') return [DASHBOARD, CRM]
  if (pathname === '/settings') return [DASHBOARD, SETTINGS]
  if (pathname === '/users') return [DASHBOARD, USERS]
  if (pathname === '/audit') return [DASHBOARD, AUDIT]

  const segments = pathname.split('/').filter(Boolean)

  if (segments[0] === 'projects' && segments.length === 1) {
    return [DASHBOARD, PROJECTS]
  }

  if (segments[0] === 'projects' && segments.length >= 2) {
    return [DASHBOARD, PROJECTS, { to: pathname, label: projectLabel ?? 'Проект' }]
  }

  if (segments[0] === 'crm' && segments.length >= 2) {
    return [DASHBOARD, CRM, { to: pathname, label: customerLabel ?? 'Клиент' }]
  }

  return [DASHBOARD]
}
