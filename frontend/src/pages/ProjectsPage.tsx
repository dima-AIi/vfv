import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { formatDateTime } from '../shared/datetime'
import { PROJECT_STATUS_LABELS, formatLabel } from '../shared/labels'
import type { Envelope, Project } from '../shared/types'
import { Badge, EmptyState, ErrorBanner, Pager, Spinner } from '../shared/ui'

const PAGE_SIZE = 10

export default function ProjectsPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [page, setPage] = useState(1)

  const projectsQuery = useQuery({
    queryKey: ['projects', page],
    queryFn: async () =>
      (
        await api.get<Envelope<Project[]>>('/projects', {
          params: { page, pageSize: PAGE_SIZE },
        })
      ).data,
  })

  const createMutation = useMutation({
    mutationFn: async (payload: { name: string; description: string; due_date?: string }) =>
      (await api.post('/projects', payload)).data,
    onSuccess: () => {
      setName('')
      setDescription('')
      setDueDate('')
      void queryClient.invalidateQueries({ queryKey: ['projects'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  if (projectsQuery.isPending) return <Spinner />
  if (projectsQuery.isError) return <ErrorBanner error={projectsQuery.error} />

  const envelope = projectsQuery.data
  const projects = envelope.data.filter((project) => showArchived || project.status === 'active')
  const pagination = envelope.meta.pagination

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim() || createMutation.isPending) return
    createMutation.mutate({
      name: name.trim(),
      description: description.trim(),
      ...(dueDate ? { due_date: dueDate } : {}),
    })
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Проекты</h1>
          <p className="page-subtitle">
            Проекты — основная рабочая область DevOS. Внутри проекта доступны задачи,
            документационный контекст и AI-ассистент.
          </p>
        </div>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Показывать архив
        </label>
      </div>

      <form className="card card-pad" style={{ marginBottom: 16 }} onSubmit={onSubmit}>
        <div className="form-row">
          <div style={{ flex: '2 1 260px' }}>
            <label className="field-label" htmlFor="project-name">
              Название проекта
            </label>
            <input
              id="project-name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Например: Внедрение внутренней CRM"
              maxLength={200}
              required
            />
          </div>
          <div style={{ flex: '3 1 320px' }}>
            <label className="field-label" htmlFor="project-description">
              Описание
            </label>
            <input
              id="project-description"
              className="input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Коротко о цели проекта"
              maxLength={5000}
            />
          </div>
          <div style={{ flex: '1 1 160px' }}>
            <label className="field-label" htmlFor="project-due-date">
              Дедлайн
            </label>
            <input
              id="project-due-date"
              className="input"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={!name.trim()}>
            Создать проект
          </button>
        </div>
        {createMutation.isError && <ErrorBanner error={createMutation.error} />}
      </form>

      {pagination && pagination.totalItems === 0 ? (
        <div className="card">
          <EmptyState
            title="Проектов нет"
            hint="Создайте проект выше — он появится в списке и в AI Workspace."
          />
        </div>
      ) : (
        <>
          <section className="card">
            {projects.map((project) => (
              <div key={project.id} className="list-row">
                <div className="list-main">
                  <Link to={`/projects/${project.id}`} style={{ textDecoration: 'none' }}>
                    <span className="list-title">{project.name}</span>
                  </Link>
                  <div className="list-desc">{project.description || '—'}</div>
                  <div className="list-meta">создан {formatDateTime(project.created_at)}</div>
                </div>
                <Badge tone={project.status === 'active' ? 'success' : 'neutral'}>
                  {formatLabel(PROJECT_STATUS_LABELS, project.status)}
                </Badge>
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
