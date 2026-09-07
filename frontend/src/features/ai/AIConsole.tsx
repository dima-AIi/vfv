import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../../shared/api'
import { formatDateTime } from '../../shared/datetime'
import { AI_ACTION_LABELS, TASK_STATUS_LABELS, formatLabel } from '../../shared/labels'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../../shared/ui'
import type {
  AIActionDetail,
  AIActionType,
  DocumentRef,
  Envelope,
  Project,
  Task,
} from '../../shared/types'
import { ActionStatusBadge, ActionTypeBadge } from './ActionBadges'

const ACTION_TYPES: { value: AIActionType; label: string; hint: string }[] = [
  { value: 'analyze', label: 'Анализ', hint: 'Разобрать задачу и контекст' },
  { value: 'plan', label: 'План', hint: 'Сформировать план действий' },
  { value: 'execute', label: 'Выполнить', hint: 'Выполнить концептуальное действие' },
  { value: 'summarize', label: 'Сводка', hint: 'Кратко свести входные данные' },
]

interface AIConsoleProps {
  fixedProjectId?: string
}

export default function AIConsole({ fixedProjectId }: AIConsoleProps) {
  const queryClient = useQueryClient()
  const [projectId, setProjectId] = useState(fixedProjectId ?? '')
  const [actionType, setActionType] = useState<AIActionType>('analyze')
  const [inputText, setInputText] = useState('')
  const [taskId, setTaskId] = useState('')
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([])
  const [openAction, setOpenAction] = useState<AIActionDetail | null>(null)

  const effectiveProjectId = fixedProjectId ?? projectId

  const projectsQuery = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => (await api.get<Envelope<Project[]>>('/projects')).data.data,
    enabled: !fixedProjectId,
  })

  const tasksQuery = useQuery<Task[]>({
    queryKey: ['tasks', effectiveProjectId],
    queryFn: async () =>
      (
        await api.get<Envelope<Task[]>>('/tasks', {
          params: { project_id: effectiveProjectId },
        })
      ).data.data,
    enabled: Boolean(effectiveProjectId),
  })

  const documentsQuery = useQuery<DocumentRef[]>({
    queryKey: ['documents', effectiveProjectId],
    queryFn: async () =>
      (
        await api.get<Envelope<DocumentRef[]>>('/documents', {
          params: { project_id: effectiveProjectId },
        })
      ).data.data,
    enabled: Boolean(effectiveProjectId),
  })

  const historyQuery = useQuery<AIActionDetail[]>({
    queryKey: ['ai-actions', effectiveProjectId],
    queryFn: async () =>
      (
        await api.get<Envelope<AIActionDetail[]>>('/ai/actions', {
          params: effectiveProjectId ? { project_id: effectiveProjectId } : {},
        })
      ).data.data,
  })

  const invalidateHistory = () => {
    void queryClient.invalidateQueries({ queryKey: ['ai-actions', effectiveProjectId] })
    void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const runMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<Envelope<AIActionDetail>>('/ai/actions', {
          action_type: actionType,
          input_text: inputText.trim(),
          ...(effectiveProjectId ? { project_id: effectiveProjectId } : {}),
          ...(taskId ? { task_id: taskId } : {}),
          document_ids: selectedDocumentIds,
        })
      ).data.data,
    onSuccess: (data: AIActionDetail) => {
      setOpenAction(data)
      setInputText('')
      invalidateHistory()
    },
  })

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!inputText.trim() || runMutation.isPending) return
    runMutation.mutate()
  }

  const activeHint = useMemo(
    () => ACTION_TYPES.find((a) => a.value === actionType)?.hint ?? '',
    [actionType],
  )

  return (
    <div className="stack">
      <form className="card card-pad" onSubmit={onSubmit}>
        <h2 className="card-title">Действие с AI-ассистентом</h2>

        {!fixedProjectId && (
          <div className="form-row" style={{ marginBottom: 12 }}>
            <div style={{ flex: '2 1 280px' }}>
              <label className="field-label" htmlFor="ai-project">
                Проект (контекст)
              </label>
              <select
                id="ai-project"
                className="select"
                value={projectId}
                onChange={(e) => {
                  setProjectId(e.target.value)
                  setTaskId('')
                  setSelectedDocumentIds([])
                }}
              >
                <option value="">— без проекта —</option>
                {(projectsQuery.data ?? []).map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ flex: '2 1 280px' }}>
              <label className="field-label" htmlFor="ai-task">
                Связанная задача (необязательно)
              </label>
              <select
                id="ai-task"
                className="select"
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                disabled={!effectiveProjectId}
              >
                <option value="">—</option>
                {(tasksQuery.data ?? []).map((task) => (
                  <option key={task.id} value={task.id}>
                    {task.title} ({formatLabel(TASK_STATUS_LABELS, task.status)})
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        <div className="form-row" style={{ marginBottom: 12 }}>
          <div style={{ flex: '0 1 220px' }}>
            <label className="field-label" htmlFor="ai-action-type">
              Тип действия
            </label>
            <select
              id="ai-action-type"
              className="select"
              value={actionType}
              onChange={(e) => setActionType(e.target.value as AIActionType)}
            >
              {ACTION_TYPES.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </select>
          </div>
          <span className="muted" style={{ alignSelf: 'flex-end', paddingBottom: 10 }}>
            {activeHint}
          </span>
        </div>

        <label className="field-label" htmlFor="ai-input">
          Формулировка задачи для AI
        </label>
        <textarea
          id="ai-input"
          className="textarea"
          rows={3}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Например: Проанализировать готовность проекта к MVP и предложить следующие шаги"
          maxLength={20000}
          required
        />

        {Boolean(documentsQuery.data?.length) && (
          <>
            <p className="field-label" style={{ marginTop: 12 }}>
              Контекст документации ({documentsQuery.data!.length})
            </p>
            <div
              style={{
                maxHeight: 150,
                overflowY: 'auto',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 10px',
              }}
            >
              {documentsQuery.data!.map((doc) => (
                <label key={doc.id} className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={selectedDocumentIds.includes(doc.id)}
                    onChange={(e) =>
                      setSelectedDocumentIds((current) =>
                        e.target.checked
                          ? [...current, doc.id]
                          : current.filter((id) => id !== doc.id),
                      )
                    }
                  />
                  <span>
                    <strong>{doc.title}</strong>{' '}
                    <span className="mono muted">{doc.relative_path}</span>
                  </span>
                </label>
              ))}
            </div>
          </>
        )}

        <div className="row-between" style={{ marginTop: 14 }}>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={!inputText.trim() || runMutation.isPending}
          >
            {runMutation.isPending ? 'Выполняется…' : `Запустить: ${AI_ACTION_LABELS[actionType]}`}
          </button>
          <span className="muted">провайдер: mock · результат сохраняется в истории</span>
        </div>
        {runMutation.isError && <ErrorBanner error={runMutation.error} />}
      </form>

      {runMutation.isPending && (
        <section className="card card-pad">
          <Spinner />
          <p className="muted" style={{ textAlign: 'center' }}>
            Действие выполняется…
          </p>
        </section>
      )}

      {!runMutation.isPending && openAction && (
        <section className="card card-pad">
          <div className="row-between" style={{ marginBottom: 10 }}>
            <h2 className="card-title" style={{ margin: 0 }}>
              Результат
            </h2>
            <div className="topbar-actions">
              <ActionTypeBadge type={openAction.action_type} />
              <ActionStatusBadge status={openAction.status} />
              {openAction.context_summary && (
                <Badge tone="neutral">{openAction.context_summary}</Badge>
              )}
            </div>
          </div>
          {openAction.status === 'failed' ? (
            <ErrorBanner error={openAction.error || 'Действие завершилось ошибкой.'} />
          ) : openAction.result ? (
            <div className="markdown-body ai-result-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{openAction.result.content}</ReactMarkdown>
            </div>
          ) : (
            <EmptyState title="Результат отсутствует" />
          )}
        </section>
      )}

      <section className="card">
        <div className="card-pad" style={{ paddingBottom: 0 }}>
          <h2 className="card-title">История действий</h2>
        </div>
        {historyQuery.isPending ? (
          <Spinner />
        ) : (historyQuery.data ?? []).length === 0 ? (
          <EmptyState
            title="История пуста"
            hint="Запустите первое AI-действие — оно появится здесь и сохранится."
          />
        ) : (
          (historyQuery.data ?? []).map((action) => (
            <button
              key={action.id}
              type="button"
              className="list-row list-row-button"
              onClick={() => setOpenAction(action)}
            >
              <div className="list-main">
                <span className="list-title">
                  {formatLabel(AI_ACTION_LABELS, action.action_type)}
                </span>
                <div className="list-desc">{action.input_text}</div>
                <div className="list-meta">
                  {formatDateTime(action.created_at)}
                  {action.result ? ` · ${action.result.summary}` : ''}
                </div>
              </div>
              <ActionStatusBadge status={action.status} />
            </button>
          ))
        )}
      </section>
    </div>
  )
}
