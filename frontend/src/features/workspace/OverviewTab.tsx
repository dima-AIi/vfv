import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api'
import { formatDateTime } from '../../shared/datetime'
import { PROJECT_STATUS_LABELS, TASK_STATUS_LABELS, formatLabel } from '../../shared/labels'
import type {
  Envelope,
  MemberOut,
  MeOut,
  Project,
  ProjectMemberOut,
  Task,
} from '../../shared/types'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../../shared/ui'
import TaskDueDate from './TaskDueDate'
import { TASK_STATUS_TONES } from './taskMeta'

const RECENT_TASKS_LIMIT = 5

function todayIso(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

export default function OverviewTab({ project }: { project: Project }) {
  const tasksQuery = useQuery<Task[]>({
    queryKey: ['tasks', project.id, 'overview'],
    queryFn: async () =>
      (
        await api.get<Envelope<Task[]>>('/tasks', {
          params: { project_id: project.id, pageSize: RECENT_TASKS_LIMIT },
        })
      ).data.data,
  })

  return (
    <div className="grid-2">
      <section className="card card-pad">
        <h2 className="card-title">Состояние проекта</h2>
        <dl style={{ margin: 0, display: 'grid', gap: 10 }}>
          <div>
            <dt className="muted">Название</dt>
            <dd style={{ margin: 0, fontWeight: 600 }}>{project.name}</dd>
          </div>
          <div>
            <dt className="muted">Статус</dt>
            <dd style={{ margin: 0 }}>
              <Badge tone={project.status === 'active' ? 'success' : 'neutral'}>
                {formatLabel(PROJECT_STATUS_LABELS, project.status)}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="muted">Дедлайн</dt>
            <dd style={{ margin: 0 }}>
              <ProjectDueDate project={project} />
            </dd>
          </div>
          <div>
            <dt className="muted">Создан</dt>
            <dd style={{ margin: 0 }}>{formatDateTime(project.created_at)}</dd>
          </div>
          <div>
            <dt className="muted">Обновлён</dt>
            <dd style={{ margin: 0 }}>{formatDateTime(project.updated_at)}</dd>
          </div>
        </dl>
      </section>

      <MembersSection projectId={project.id} />

      <section className="card">
        <div className="card-pad" style={{ paddingBottom: 0 }}>
          <h2 className="card-title">Задачи</h2>
        </div>
        {tasksQuery.isPending && <Spinner />}
        {tasksQuery.isError && <ErrorBanner error={tasksQuery.error} />}
        {!tasksQuery.isPending && !tasksQuery.isError && (tasksQuery.data ?? []).length === 0 && (
          <EmptyState title="Задач нет" hint="Создайте первую задачу на вкладке «Задачи»." />
        )}
        {(tasksQuery.data ?? []).map((task) => (
          <div key={task.id} className="list-row">
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
              <div className="list-meta">исполнитель {task.assignee_name ?? '—'}</div>
            </div>
            <div className="topbar-actions">
              <TaskDueDate task={task} />
              <Badge tone={TASK_STATUS_TONES[task.status]}>
                {formatLabel(TASK_STATUS_LABELS, task.status)}
              </Badge>
            </div>
          </div>
        ))}
      </section>

      <section className="card card-pad">
        <h2 className="card-title">Как здесь работать</h2>
        <ol
          style={{
            margin: 0,
            paddingLeft: 18,
            color: 'var(--text-secondary)',
            display: 'grid',
            gap: 8,
          }}
        >
          <li>Вкладка «Задачи» — ведите задачи проекта: исполнитель, дедлайн, комментарии.</li>
          <li>Вкладка «Документация» — подключите markdown-контекст из документации DevOS.</li>
          <li>Вкладка «AI-ассистент» — выберите тип действия, контекст и запустите анализ.</li>
          <li>Результаты действий сохраняются вместе с проектом.</li>
        </ol>
      </section>
    </div>
  )
}

function ProjectDueDate({ project }: { project: Project }) {
  const queryClient = useQueryClient()
  const overdue =
    project.due_date !== null && project.due_date < todayIso() && project.status === 'active'

  const mutation = useMutation({
    mutationFn: async (value: string | null) =>
      (await api.patch(`/projects/${project.id}`, { due_date: value })).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['project', project.id] })
      void queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <input
        className="input"
        type="date"
        style={{ width: 170 }}
        defaultValue={project.due_date ?? ''}
        key={`proj-due-${project.due_date ?? ''}`}
        aria-label="Дедлайн проекта"
        onChange={(e) => mutation.mutate(e.target.value || null)}
      />
      {overdue && <span className="badge badge-overdue">просрочено</span>}
      {mutation.isError && <ErrorBanner error={mutation.error} />}
    </div>
  )
}

function MembersSection({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()
  const [selectedMemberId, setSelectedMemberId] = useState('')

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
  })
  const orgId = meQuery.data?.organization_id ?? null

  const membersQuery = useQuery<ProjectMemberOut[]>({
    queryKey: ['project-members', projectId],
    queryFn: async () =>
      (await api.get<Envelope<ProjectMemberOut[]>>(`/projects/${projectId}/members`)).data.data,
  })

  const orgMembersQuery = useQuery<MemberOut[]>({
    queryKey: ['organization-members', orgId],
    queryFn: async () =>
      (await api.get<Envelope<MemberOut[]>>(`/organizations/${orgId}/members`)).data.data,
    enabled: Boolean(orgId),
  })

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ['project-members', projectId] })

  const addMutation = useMutation({
    mutationFn: async (userId: string) =>
      (await api.post(`/projects/${projectId}/members`, { userId })).data,
    onSuccess: () => {
      setSelectedMemberId('')
      invalidate()
    },
  })

  const removeMutation = useMutation({
    mutationFn: async (userId: string) => api.delete(`/projects/${projectId}/members/${userId}`),
    onSuccess: invalidate,
  })

  const currentIds = new Set((membersQuery.data ?? []).map((m) => m.id))
  const candidates = (orgMembersQuery.data ?? []).filter((m) => !currentIds.has(m.id))

  return (
    <section className="card card-pad">
      <h2 className="card-title">Участники</h2>
      {membersQuery.isPending && <Spinner />}
      {membersQuery.isError && <ErrorBanner error={membersQuery.error} />}
      {!membersQuery.isPending &&
        !membersQuery.isError &&
        (membersQuery.data ?? []).length === 0 && (
          <p className="muted" style={{ margin: '0 0 10px' }}>
            Участников пока нет.
          </p>
        )}
      <div className="topbar-actions" style={{ flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
        {(membersQuery.data ?? []).map((member) => (
          <span key={member.id} className="badge badge-accent" style={{ gap: 6 }}>
            {member.display_name}
            <button
              onClick={() => removeMutation.mutate(member.id)}
              disabled={removeMutation.isPending}
              aria-label={`Удалить участника ${member.display_name}`}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'inherit',
                padding: 0,
              }}
            >
              ✕
            </button>
          </span>
        ))}
      </div>
      <div className="form-row">
        <div style={{ flex: '2 1 220px' }}>
          <label className="field-label" htmlFor="add-member-select">
            Добавить участника
          </label>
          <select
            id="add-member-select"
            className="select"
            value={selectedMemberId}
            onChange={(e) => setSelectedMemberId(e.target.value)}
          >
            <option value="">— выберите —</option>
            {candidates.map((member) => (
              <option key={member.id} value={member.id}>
                {member.display_name}
              </option>
            ))}
          </select>
        </div>
        <button
          className="btn btn-primary"
          style={{ alignSelf: 'flex-end' }}
          disabled={!selectedMemberId || addMutation.isPending}
          onClick={() => selectedMemberId && addMutation.mutate(selectedMemberId)}
        >
          Добавить
        </button>
      </div>
      {addMutation.isError && <ErrorBanner error={addMutation.error} />}
      {removeMutation.isError && <ErrorBanner error={removeMutation.error} />}
    </section>
  )
}
