import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, useSearchParams } from 'react-router-dom'
import { api } from '../shared/api'
import { PROJECT_STATUS_LABELS, formatLabel } from '../shared/labels'
import { Badge, ErrorBanner, Spinner } from '../shared/ui'
import type { Envelope, Project } from '../shared/types'
import OverviewTab from '../features/workspace/OverviewTab'
import TasksTab from '../features/workspace/TasksTab'
import DocumentsTab from '../features/documents/DocumentsTab'
import AIConsole from '../features/ai/AIConsole'

const TABS = [
  { key: 'overview', label: 'Обзор' },
  { key: 'tasks', label: 'Задачи' },
  { key: 'documents', label: 'Документация' },
  { key: 'ai', label: 'AI-ассистент' },
] as const

type TabKey = (typeof TABS)[number]['key']

function isTabKey(value: string | null): value is TabKey {
  return TABS.some((tab) => tab.key === value)
}

export default function ProjectWorkspacePage() {
  const { projectId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const activeTab: TabKey = isTabKey(requestedTab) ? requestedTab : TABS[0].key

  useEffect(() => {
    if (requestedTab !== null && !isTabKey(requestedTab)) {
      setSearchParams({}, { replace: true })
    }
  }, [requestedTab, setSearchParams])

  const projectQuery = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: async () => (await api.get<Envelope<Project>>(`/projects/${projectId}`)).data.data,
    enabled: Boolean(projectId),
  })

  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)

  if (!projectId) return <ErrorBanner error="Отсутствует идентификатор проекта." />
  if (projectQuery.isPending) return <Spinner />
  if (projectQuery.isError) return <ErrorBanner error={projectQuery.error} />

  const project = projectQuery.data

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">{project.name}</h1>
          <p className="page-subtitle">{project.description || 'Описание не задано.'}</p>
        </div>
        <Badge tone={project.status === 'active' ? 'success' : 'neutral'}>
          {formatLabel(PROJECT_STATUS_LABELS, project.status)}
        </Badge>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`tab${activeTab === tab.key ? ' active' : ''}`}
            onClick={() => setSearchParams({ tab: tab.key })}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && <OverviewTab project={project} />}
      {activeTab === 'tasks' && <TasksTab projectId={projectId} />}
      {activeTab === 'documents' && (
        <DocumentsTab
          projectId={projectId}
          selectedDocumentId={selectedDocumentId}
          onSelectDocument={setSelectedDocumentId}
        />
      )}
      {activeTab === 'ai' && <AIConsole fixedProjectId={projectId} />}
    </>
  )
}
