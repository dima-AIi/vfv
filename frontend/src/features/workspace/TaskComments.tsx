import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api'
import { formatDateTime } from '../../shared/datetime'
import type { Comment, Envelope, MeOut } from '../../shared/types'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../../shared/ui'

interface TaskCommentsProps {
  taskId: string
}

export default function TaskComments({ taskId }: TaskCommentsProps) {
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
  })

  const commentsQuery = useQuery<Comment[]>({
    queryKey: ['task-comments', taskId],
    queryFn: async () =>
      (await api.get<Envelope<Comment[]>>(`/tasks/${taskId}/comments`)).data.data,
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['task-comments', taskId] })
    void queryClient.invalidateQueries({ queryKey: ['task', taskId] })
  }

  const createMutation = useMutation({
    mutationFn: async (payload: { body: string }) =>
      (await api.post(`/tasks/${taskId}/comments`, payload)).data,
    onSuccess: () => {
      setBody('')
      invalidate()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/comments/${id}`),
    onSuccess: invalidate,
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!body.trim() || createMutation.isPending) return
    createMutation.mutate({ body: body.trim() })
  }

  const me = meQuery.data
  const comments = commentsQuery.data ?? []

  return (
    <div style={{ padding: '12px 20px 16px' }}>
      <h3 className="card-title" style={{ marginTop: 0 }}>
        Комментарии
      </h3>
      {commentsQuery.isPending && <Spinner />}
      {commentsQuery.isError && <ErrorBanner error={commentsQuery.error} />}
      {!commentsQuery.isPending && !commentsQuery.isError && comments.length === 0 && (
        <EmptyState title="Комментариев нет" hint="Добавьте первый комментарий к задаче." />
      )}
      {comments.map((comment) => (
        <div key={comment.id} className="list-row" style={{ padding: '10px 4px' }}>
          <div className="list-main">
            <span className="list-title">{comment.author_name ?? '—'}</span>
            <div className="comment-meta">{formatDateTime(comment.created_at)}</div>
            <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{comment.body}</div>
          </div>
          {me && comment.author_id === me.id && (
            <div className="topbar-actions">
              <Badge tone="neutral">ваш</Badge>
              <button
                className="btn btn-danger-ghost"
                onClick={() => deleteMutation.mutate(comment.id)}
                disabled={deleteMutation.isPending}
                aria-label="Удалить комментарий"
              >
                Удалить
              </button>
            </div>
          )}
        </div>
      ))}
      <form onSubmit={onSubmit} style={{ marginTop: 12 }}>
        <label className="field-label" htmlFor={`comment-body-${taskId}`}>
          Новый комментарий
        </label>
        <textarea
          id={`comment-body-${taskId}`}
          className="textarea"
          rows={2}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Добавьте комментарий…"
          maxLength={5000}
          required
        />
        <div className="topbar-actions" style={{ marginTop: 10 }}>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={!body.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? 'Отправка…' : 'Добавить'}
          </button>
          <span className="muted">комментарий сохраняется вместе с задачей</span>
        </div>
        {createMutation.isError && <ErrorBanner error={createMutation.error} />}
        {deleteMutation.isError && <ErrorBanner error={deleteMutation.error} />}
      </form>
    </div>
  )
}
