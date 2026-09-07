import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api'
import { formatDateTime } from '../../shared/datetime'
import type { Envelope, TaskAttachmentOut } from '../../shared/types'
import { EmptyState, ErrorBanner, Spinner } from '../../shared/ui'

function formatBytes(size: number): string {
  if (size < 1024) return `${size} Б`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} КБ`
  return `${(size / (1024 * 1024)).toFixed(1)} МБ`
}

export default function TaskAttachments({ taskId }: { taskId: string }) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)

  const attachmentsQuery = useQuery<TaskAttachmentOut[]>({
    queryKey: ['task-attachments', taskId],
    queryFn: async () =>
      (await api.get<Envelope<TaskAttachmentOut[]>>(`/tasks/${taskId}/attachments`)).data.data,
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['task-attachments', taskId] })
    void queryClient.invalidateQueries({ queryKey: ['task', taskId] })
  }

  const attachMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const uploaded = await api.post('/files', form)
      const fileId = (uploaded.data.data as { id: string }).id
      return api.post(`/tasks/${taskId}/attachments`, { fileId })
    },
    onSuccess: () => {
      setBusy(false)
      invalidate()
    },
    onError: () => setBusy(false),
  })

  const detachMutation = useMutation({
    mutationFn: async (attachmentId: string) =>
      api.delete(`/tasks/${taskId}/attachments/${attachmentId}`),
    onSuccess: invalidate,
  })

  const onFilePicked = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setBusy(true)
    attachMutation.mutate(file)
  }

  const downloadFile = async (fileId: string, name: string) => {
    const response = await api.get<Blob>(`/files/${fileId}/content`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = name
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  }

  const attachments = attachmentsQuery.data ?? []

  return (
    <div style={{ padding: '12px 20px 16px' }}>
      <h3 className="card-title" style={{ marginTop: 0 }}>
        Вложения
      </h3>
      {attachmentsQuery.isPending && <Spinner />}
      {attachmentsQuery.isError && <ErrorBanner error={attachmentsQuery.error} />}
      {!attachmentsQuery.isPending && !attachmentsQuery.isError && attachments.length === 0 && (
        <EmptyState title="Вложений нет" hint="Прикрепите файл к задаче." />
      )}
      {attachments.map((attachment) => (
        <div key={attachment.id} className="list-row" style={{ padding: '10px 4px' }}>
          <div className="list-main">
            <span className="list-title">{attachment.filename}</span>
            <div className="comment-meta">
              {formatBytes(attachment.size_bytes)} · {formatDateTime(attachment.created_at)} ·{' '}
              {attachment.created_by_name ?? '—'}
            </div>
          </div>
          <div className="topbar-actions">
            <button
              className="btn btn-ghost"
              onClick={() => void downloadFile(attachment.file_id, attachment.filename)}
            >
              Скачать
            </button>
            <button
              className="btn btn-danger-ghost"
              onClick={() => detachMutation.mutate(attachment.id)}
              disabled={detachMutation.isPending}
              aria-label={`Открепить ${attachment.filename}`}
            >
              ✕
            </button>
          </div>
        </div>
      ))}
      <input
        ref={fileInputRef}
        type="file"
        hidden
        onChange={onFilePicked}
        aria-label="Прикрепить файл"
      />
      <div className="topbar-actions" style={{ marginTop: 12 }}>
        <button
          className="btn btn-primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={busy}
        >
          {busy ? 'Загрузка…' : 'Прикрепить файл'}
        </button>
      </div>
      {attachMutation.isError && <ErrorBanner error={attachMutation.error} />}
      {detachMutation.isError && <ErrorBanner error={detachMutation.error} />}
    </div>
  )
}
