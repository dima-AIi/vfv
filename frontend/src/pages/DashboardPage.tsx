import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import type { Dashboard, Envelope } from '../shared/types'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../shared/ui'
import { ActionStatusBadge } from '../features/ai/ActionBadges'
import { AI_ACTION_LABELS, PROJECT_STATUS_LABELS, formatLabel } from '../shared/labels'

function useDashboard() {
  return useQuery<Dashboard>({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<Envelope<Dashboard>>('/dashboard')).data.data,
  })
}

export default function DashboardPage() {
  const { data, isPending, isError, error } = useDashboard()

  if (isPending) return <Spinner />
  if (isError) return <ErrorBanner error={error} />
  if (!data) return null

  const stats = [
    { label: 'Проекты', value: data.stats.projects },
    { label: 'Задачи', value: data.stats.tasks },
    { label: 'Документы', value: data.stats.documents },
    { label: 'AI-действия', value: data.stats.ai_actions },
  ]

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Панель</h1>
          <p className="page-subtitle">
            Обзор рабочего пространства DevOS: проекты, задачи, документационный контекст и история
            AI-действий.
          </p>
        </div>
      </div>

      <div className="stat-grid">
        {stats.map((s) => (
          <div key={s.label} className="card stat-card">
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-pad" style={{ paddingBottom: 0 }}>
            <h2 className="card-title">Последние проекты</h2>
          </div>
          {data.recent_projects.length === 0 ? (
            <EmptyState
              title="Пока нет проектов"
              hint="Создайте первый проект в разделе «Проекты»."
              action={
                <Link to="/projects" className="btn btn-primary" style={{ marginTop: 10 }}>
                  Открыть проекты
                </Link>
              }
            />
          ) : (
            data.recent_projects.map((project) => (
              <div key={project.id} className="list-row">
                <div className="list-main">
                  <Link to={`/projects/${project.id}`} style={{ textDecoration: 'none' }}>
                    <span className="list-title">{project.name}</span>
                  </Link>
                  <div className="list-desc">{project.description || '—'}</div>
                </div>
                <Badge tone={project.status === 'active' ? 'success' : 'neutral'}>
                  {formatLabel(PROJECT_STATUS_LABELS, project.status)}
                </Badge>
              </div>
            ))
          )}
        </section>

        <section className="card">
          <div className="card-pad" style={{ paddingBottom: 0 }}>
            <h2 className="card-title">Последние AI-действия</h2>
          </div>
          {data.recent_ai_actions.length === 0 ? (
            <EmptyState
              title="AI ещё не выполнял действий"
              hint="Запустите первое действие в разделе «AI-ассистент»."
              action={
                <Link to="/ai" className="btn btn-ghost" style={{ marginTop: 10 }}>
                  Открыть AI-ассистент
                </Link>
              }
            />
          ) : (
            data.recent_ai_actions.map((action) => (
              <div key={action.id} className="list-row">
                <div className="list-main">
                  <div className="list-title">
                    {formatLabel(AI_ACTION_LABELS, action.action_type)}
                  </div>
                  <div className="list-desc">{action.input_text}</div>
                </div>
                <ActionStatusBadge status={action.status} />
              </div>
            ))
          )}
        </section>
      </div>
    </>
  )
}
