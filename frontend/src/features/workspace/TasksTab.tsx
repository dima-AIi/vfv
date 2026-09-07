import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api'
import { formatDateTime } from '../../shared/datetime'
import { TASK_PRIORITY_LABELS, TASK_STATUS_LABELS, formatLabel } from '../../shared/labels'
import type { Envelope, MemberOut, MeOut, Task, TaskPriority, TaskStatus } from '../../shared/types'
import { Badge, EmptyState, ErrorBanner, Pager, Spinner } from '../../shared/ui'
import TaskAttachments from './TaskAttachments'
import TaskComments from './TaskComments'
import TaskDueDate from './TaskDueDate'
import { TASK_STATUS_TONES } from './taskMeta'

const PAGE_SIZE = 10

export default function TasksTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<TaskPriority>('medium')
  const [dueDate, setDueDate] = useState('')
  const [assigneeId, setAssigneeId] = useState('')
  const [page, setPage] = useState(1)
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null)

  const tasksQuery = useQuery({
    queryKey: ['tasks', projectId, page],
    queryFn: async () =>
      (
        await api.get<Envelope<Task[]>>('/tasks', {
          params: { project_id: projectId, page, pageSize: PAGE_SIZE },
        })
      ).data,
  })

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
  })

  const organizationId = meQuery.data?.organization_id ?? null

  const membersQuery = useQuery<MemberOut[]>({
    queryKey: ['organization-members', organizationId],
    queryFn: async () =>
      (await api.get<Envelope<MemberOut[]>>(`/organizations/${organizationId}/members`)).data.data,
    enabled: Boolean(organizationId),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
    void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const createMutation = useMutation({
    mutationFn: async (payload: {
      project_id: string
      title: string
      priority: TaskPriority
      due_date?: string
      assignee_id?: string
    }) => (await api.post('/tasks', payload)).data,
    onSuccess: () => {
      setTitle('')
      setPriority('medium')
      setDueDate('')
      setAssigneeId('')
      invalidate()
    },
  })

  const statusMutation = useMutation({
    mutationFn: async (payload: { id: string; status: TaskStatus }) =>
      (await api.patch(`/tasks/${payload.id}`, { status: payload.status })).data,
    onSuccess: invalidate,
  })

  const editMutation = useMutation({
    mutationFn: async (payload: { id: string; due_date?: string; assignee_id?: string }) => {
      const { id, ...body } = payload
      return (await api.patch(`/tasks/${id}`, body)).data
    },
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/tasks/${id}`),
    onSuccess: invalidate,
  })

  if (tasksQuery.isPending) return <Spinner />
  if (tasksQuery.isError) return <ErrorBanner error={tasksQuery.error} />

  const tasks = tasksQuery.data.data
  const pagination = tasksQuery.data.meta.pagination

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!title.trim() || createMutation.isPending) return
    createMutation.mutate({
      project_id: projectId,
      title: title.trim(),
      priority,
      ...(dueDate ? { due_date: dueDate } : {}),
      ...(assigneeId ? { assignee_id: assigneeId } : {}),
    })
  }

  return (
    <>
      <form className="card card-pad" style={{ marginBottom: 16 }} onSubmit={onSubmit}>
        <div className="form-row">
          <div style={{ flex: '3 1 280px' }}>
            <label className="field-label" htmlFor="task-title">
              Новая задача
            </label>
            <input
              id="task-title"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Что нужно сделать?"
              maxLength={300}
              required
            />
          </div>
          <div style={{ flex: '1 1 140px' }}>
            <label className="field-label" htmlFor="task-priority">
              Приоритет
            </label>
            <select
              id="task-priority"
              className="select"
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
            >
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
            </select>
          </div>
          <div style={{ flex: '1 1 150px' }}>
            <label className="field-label" htmlFor="task-due-date">
              Дедлайн
            </label>
            <input
              id="task-due-date"
              className="input"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>
          <div style={{ flex: '1 1 180px' }}>
            <label className="field-label" htmlFor="task-assignee">
              Исполнитель
            </label>
            <select
              id="task-assignee"
              className="select"
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
            >
              <option value="">— не назначен —</option>
              {(membersQuery.data ?? []).map((member) => (
                <option key={member.id} value={member.id}>
                  {member.display_name}
                </option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary" type="submit" disabled={!title.trim()}>
            Добавить задачу
          </button>
        </div>
        {createMutation.isError && <ErrorBanner error={createMutation.error} />}
        {statusMutation.isError && <ErrorBanner error={statusMutation.error} />}
        {editMutation.isError && <ErrorBanner error={editMutation.error} />}
        {deleteMutation.isError && <ErrorBanner error={deleteMutation.error} />}
      </form>

      {tasks.length === 0 && page === 1 ? (
        <div className="card">
          <EmptyState title="Задач нет" hint="Добавьте первую задачу проекта." />
        </div>
      ) : (
        <>
          <section className="card">
            {tasks.map((task) => (
              <div key={task.id}>
                <div
                  className="list-row"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                >
                  <div className="list-main">
                    <span
                      className="list-title"
                      style={{
                        textDecoration: task.status === 'done' ? 'line-through' : undefined,
                        color: task.status === 'done' ? 'var(--text-muted)' : undefined,
                      }}
                    >
                      {task.title}
                    </span>
                    <div className="list-meta">
                      создана {formatDateTime(task.created_at)} · приоритет{' '}
                      {formatLabel(TASK_PRIORITY_LABELS, task.priority)}
                    </div>
                  </div>
                  <div style={{ minWidth: 110 }}>
                    <div className="muted" style={{ fontSize: 11 }}>
                      Исполнитель
                    </div>
                    <div>{task.assignee_name ?? '—'}</div>
                  </div>
                  <div style={{ minWidth: 130 }}>
                    <div className="muted" style={{ fontSize: 11 }}>
                      Дедлайн
                    </div>
                    <TaskDueDate task={task} />
                  </div>
                  <div className="topbar-actions" onClick={(e) => e.stopPropagation()}>
                    <select
                      className="select"
                      style={{ width: 140 }}
                      aria-label={`Статус задачи ${task.title}`}
                      value={task.status}
                      onChange={(e) =>
                        statusMutation.mutate({
                          id: task.id,
                          status: e.target.value as TaskStatus,
                        })
                      }
                    >
                      <option value="open">Открыта</option>
                      <option value="in_progress">В работе</option>
                      <option value="done">Готово</option>
                    </select>
                    <Badge tone={TASK_STATUS_TONES[task.status]}>
                      {formatLabel(TASK_STATUS_LABELS, task.status)}
                    </Badge>
                    <button
                      className="btn btn-danger-ghost"
                      onClick={() => deleteMutation.mutate(task.id)}
                      disabled={deleteMutation.isPending}
                      aria-label={`Удалить задачу ${task.title}`}
                    >
                      Удалить
                    </button>
                  </div>
                </div>
                {expandedTaskId === task.id && (
                  <div className="card" style={{ margin: '0 20px 12px', overflow: 'hidden' }}>
                    <div style={{ padding: '12px 20px 0' }}>
                      <div className="form-row">
                        <div style={{ flex: '1 1 150px' }}>
                          <label className="field-label" htmlFor={`due-${task.id}`}>
                            Дедлайн
                          </label>
                          <input
                            id={`due-${task.id}`}
                            className="input"
                            type="date"
                            defaultValue={task.due_date ?? ''}
                            key={`due-${task.id}-${task.due_date ?? ''}`}
                            onChange={(e) =>
                              editMutation.mutate({
                                id: task.id,
                                ...(e.target.value ? { due_date: e.target.value } : {}),
                              })
                            }
                          />
                        </div>
                        <div style={{ flex: '1 1 200px' }}>
                          <label className="field-label" htmlFor={`assignee-${task.id}`}>
                            Исполнитель
                          </label>
                          <select
                            id={`assignee-${task.id}`}
                            className="select"
                            defaultValue={task.assignee_id ?? ''}
                            key={`assignee-${task.id}-${task.assignee_id ?? ''}`}
                            onChange={(e) =>
                              editMutation.mutate({
                                id: task.id,
                                ...(e.target.value ? { assignee_id: e.target.value } : {}),
                              })
                            }
                          >
                            <option value="">— не назначен —</option>
                            {(membersQuery.data ?? []).map((member) => (
                              <option key={member.id} value={member.id}>
                                {member.display_name}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div className="comment-meta" style={{ margin: '6px 0 10px' }}>
                        Изменения сохраняются сразу после выбора значения.
                      </div>
                    </div>
                    <TaskComments taskId={task.id} />
                    <TaskAttachments taskId={task.id} />
                  </div>
                )}
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
