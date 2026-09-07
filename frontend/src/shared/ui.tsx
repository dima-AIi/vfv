import type { ReactNode } from 'react'
import { getApiError } from './errors'
import type { PaginationMeta } from './types'

export function Badge({
  tone,
  children,
}: {
  tone: 'neutral' | 'success' | 'warning' | 'danger' | 'accent'
  children: ReactNode
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function Spinner() {
  return <div className="spinner" role="status" aria-label="Загрузка" />
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string
  hint?: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      {hint && <p>{hint}</p>}
      {action}
    </div>
  )
}

export function ErrorBanner({ error }: { error: unknown }) {
  const view = getApiError(error)
  return (
    <div className="error-banner" role="alert">
      {view.message}
      {view.code && (
        <span className="muted" style={{ marginLeft: 8 }}>
          [{view.code}]
        </span>
      )}
    </div>
  )
}

export function Pager({
  pagination,
  onPageChange,
}: {
  pagination: PaginationMeta
  onPageChange: (page: number) => void
}) {
  if (pagination.totalItems === 0) return null
  return (
    <div className="topbar-actions" style={{ marginTop: 14 }}>
      <button
        className="btn btn-ghost"
        disabled={!pagination.hasPrevious}
        onClick={() => onPageChange(pagination.page - 1)}
      >
        ‹ Назад
      </button>
      <span className="muted">
        страница {pagination.page} из {pagination.totalPages}
      </span>
      <button
        className="btn btn-ghost"
        disabled={!pagination.hasNext}
        onClick={() => onPageChange(pagination.page + 1)}
      >
        Вперёд ›
      </button>
    </div>
  )
}
