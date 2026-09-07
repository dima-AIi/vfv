import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../shared/api'
import { formatDateTime } from '../shared/datetime'
import type { AuditRecordOut, Envelope } from '../shared/types'
import { EmptyState, ErrorBanner, Pager, Spinner } from '../shared/ui'

const PAGE_SIZE = 20

export default function AuditPage() {
  const [actionType, setActionType] = useState('')
  const [entityType, setEntityType] = useState('')
  const [createdAfter, setCreatedAfter] = useState('')
  const [createdBefore, setCreatedBefore] = useState('')
  const [page, setPage] = useState(1)

  const auditQuery = useQuery<Envelope<AuditRecordOut[]>>({
    queryKey: ['audit', page, actionType, entityType, createdAfter, createdBefore],
    queryFn: async () =>
      (
        await api.get<Envelope<AuditRecordOut[]>>('/audit', {
          params: {
            page,
            pageSize: PAGE_SIZE,
            ...(actionType.trim() ? { action_type: actionType.trim() } : {}),
            ...(entityType.trim() ? { entity_type: entityType.trim() } : {}),
            ...(createdAfter ? { createdAfter: `${createdAfter}T00:00:00` } : {}),
            ...(createdBefore ? { createdBefore: `${createdBefore}T23:59:59` } : {}),
          },
        })
      ).data,
  })

  if (auditQuery.isPending) return <Spinner />
  if (auditQuery.isError) return <ErrorBanner error={auditQuery.error} />

  const envelope = auditQuery.data
  const records = envelope.data
  const pagination = envelope.meta.pagination

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Аудит</h1>
          <p className="page-subtitle">Журнал действий платформы с фильтрами по времени и типу.</p>
        </div>
      </div>

      <div className="card card-pad" style={{ marginBottom: 16 }}>
        <div className="form-row">
          <div style={{ flex: '1 1 160px' }}>
            <label className="field-label" htmlFor="audit-action">
              Действие
            </label>
            <input
              id="audit-action"
              className="input"
              value={actionType}
              placeholder="LOGIN_SUCCESS"
              onChange={(e) => {
                setActionType(e.target.value)
                setPage(1)
              }}
            />
          </div>
          <div style={{ flex: '1 1 160px' }}>
            <label className="field-label" htmlFor="audit-entity">
              Сущность
            </label>
            <input
              id="audit-entity"
              className="input"
              value={entityType}
              placeholder="user"
              onChange={(e) => {
                setEntityType(e.target.value)
                setPage(1)
              }}
            />
          </div>
          <div style={{ flex: '1 1 160px' }}>
            <label className="field-label" htmlFor="audit-after">
              С даты
            </label>
            <input
              id="audit-after"
              className="input"
              type="date"
              value={createdAfter}
              onChange={(e) => {
                setCreatedAfter(e.target.value)
                setPage(1)
              }}
            />
          </div>
          <div style={{ flex: '1 1 160px' }}>
            <label className="field-label" htmlFor="audit-before">
              По дату
            </label>
            <input
              id="audit-before"
              className="input"
              type="date"
              value={createdBefore}
              onChange={(e) => {
                setCreatedBefore(e.target.value)
                setPage(1)
              }}
            />
          </div>
        </div>
      </div>

      {pagination && pagination.totalItems === 0 ? (
        <div className="card">
          <EmptyState title="Записей нет" hint="Измените фильтры или подождите событий." />
        </div>
      ) : (
        <>
          <section className="card">
            {records.map((record) => (
              <div key={record.id} className="list-row">
                <div className="list-main">
                  <span className="list-title mono">{record.action_type}</span>
                  <div className="list-meta">
                    {formatDateTime(record.created_at)} · {record.entity_type}
                    {record.entity_id ? `:${record.entity_id.slice(0, 8)}` : ''} · пользователь{' '}
                    {record.user_id ? record.user_id.slice(0, 8) : '—'}
                  </div>
                  {Object.keys(record.detail).length > 0 && (
                    <div className="list-meta mono">{JSON.stringify(record.detail)}</div>
                  )}
                </div>
              </div>
            ))}
          </section>
          {pagination && (
            <Pager
              pagination={pagination}
              onPageChange={(next) => {
                setPage(next)
              }}
            />
          )}
        </>
      )}
    </>
  )
}
