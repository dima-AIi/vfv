import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../shared/api'
import { formatDateTime } from '../shared/datetime'
import type { Envelope, NotificationOut } from '../shared/types'
import { EmptyState, ErrorBanner, Pager, Spinner } from '../shared/ui'

const PAGE_SIZE = 20

export default function NotificationsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)

  const notificationsQuery = useQuery<Envelope<NotificationOut[]>>({
    queryKey: ['notifications', 'all', page],
    queryFn: async () =>
      (
        await api.get<Envelope<NotificationOut[]>>('/notifications', {
          params: { page, pageSize: PAGE_SIZE },
        })
      ).data,
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  const readAllMutation = useMutation({
    mutationFn: async () => (await api.post('/notifications/read-all')).data,
    onSuccess: invalidate,
  })

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => api.post(`/notifications/${id}/read`),
    onSuccess: invalidate,
  })

  if (notificationsQuery.isPending) return <Spinner />
  if (notificationsQuery.isError) return <ErrorBanner error={notificationsQuery.error} />

  const envelope = notificationsQuery.data
  const notifications = envelope.data
  const pagination = envelope.meta.pagination

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Уведомления</h1>
          <p className="page-subtitle">
            Центр in-app уведомлений: назначения задач и комментарии к вашим задачам.
          </p>
        </div>
        <button
          className="btn btn-ghost"
          onClick={() => readAllMutation.mutate()}
          disabled={readAllMutation.isPending}
        >
          Прочитать все
        </button>
      </div>

      {readAllMutation.isError && <ErrorBanner error={readAllMutation.error} />}
      {markReadMutation.isError && <ErrorBanner error={markReadMutation.error} />}

      {notifications.length === 0 && page === 1 ? (
        <div className="card">
          <EmptyState
            title="Уведомлений нет"
            hint="Здесь появятся новые события по вашим задачам."
          />
        </div>
      ) : (
        <section className="card">
          {notifications.map((notification) => {
            const isUnread = notification.read_at === null
            return (
              <button
                key={notification.id}
                type="button"
                className="list-row list-row-button"
                onClick={() => isUnread && markReadMutation.mutate(notification.id)}
              >
                <div className="list-main">
                  <span className="list-title" style={{ fontWeight: isUnread ? 700 : 500 }}>
                    {isUnread ? '● ' : ''}
                    {notification.title}
                  </span>
                  <div className="list-desc">{notification.body}</div>
                  <div className="list-meta">{formatDateTime(notification.created_at)}</div>
                </div>
                <span className="muted">{isUnread ? 'не прочитано' : 'прочитано'}</span>
              </button>
            )
          })}
        </section>
      )}

      {pagination && (
        <Pager
          pagination={pagination}
          onPageChange={(next) => {
            setPage(next)
          }}
        />
      )}
    </>
  )
}
