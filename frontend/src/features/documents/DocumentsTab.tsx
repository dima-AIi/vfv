import { useMemo, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../../shared/api'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../../shared/ui'
import type {
  CatalogEntry,
  DocumentContent,
  DocumentRef,
  Envelope,
  FolderOut,
} from '../../shared/types'

interface DocumentsTabProps {
  projectId: string
  selectedDocumentId: string | null
  onSelectDocument: (id: string | null) => void
}

function childrenOf(folders: FolderOut[], parentId: string | null): FolderOut[] {
  return folders.filter((folder) => folder.parent_id === parentId)
}

export default function DocumentsTab({
  projectId,
  selectedDocumentId,
  onSelectDocument,
}: DocumentsTabProps) {
  const queryClient = useQueryClient()
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)
  const [newFolderName, setNewFolderName] = useState('')
  const [rootFilter, setRootFilter] = useState<string>('all')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const foldersQuery = useQuery<FolderOut[]>({
    queryKey: ['document-folders'],
    queryFn: async () =>
      (
        await api.get<Envelope<FolderOut[]>>('/documents/folders', {
          params: { pageSize: 100 },
        })
      ).data.data,
  })

  const documentsQuery = useQuery<DocumentRef[]>({
    queryKey: ['documents', projectId, selectedFolderId],
    queryFn: async () =>
      (
        await api.get<Envelope<DocumentRef[]>>('/documents', {
          params: selectedFolderId
            ? { folder_id: selectedFolderId, pageSize: 100 }
            : { project_id: projectId, pageSize: 100 },
        })
      ).data.data,
  })

  const catalogQuery = useQuery<CatalogEntry[]>({
    queryKey: ['document-catalog'],
    queryFn: async () => (await api.get<Envelope<CatalogEntry[]>>('/documents/catalog')).data.data,
  })

  const contentQuery = useQuery<DocumentContent>({
    queryKey: ['document-content', selectedDocumentId],
    queryFn: async () =>
      (await api.get<Envelope<DocumentContent>>(`/documents/${selectedDocumentId}`)).data.data,
    enabled: Boolean(selectedDocumentId),
  })

  const invalidateDocuments = () => {
    void queryClient.invalidateQueries({ queryKey: ['documents'] })
    void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const createFolderMutation = useMutation({
    mutationFn: async (payload: { name: string; parent_id: string | null }) =>
      (await api.post('/documents/folders', payload)).data,
    onSuccess: () => {
      setNewFolderName('')
      void queryClient.invalidateQueries({ queryKey: ['document-folders'] })
    },
  })

  const deleteFolderMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/documents/folders/${id}`),
    onSuccess: (_data, id) => {
      if (selectedFolderId === id) setSelectedFolderId(null)
      void queryClient.invalidateQueries({ queryKey: ['document-folders'] })
      void queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const uploaded = await api.post('/files', form)
      const fileId = (uploaded.data.data as { id: string }).id
      return api.post('/documents', {
        title: file.name,
        file_id: fileId,
        folder_id: selectedFolderId,
        project_id: projectId,
        category: 'files',
      })
    },
    onSuccess: invalidateDocuments,
  })

  const attachMutation = useMutation({
    mutationFn: async (entry: CatalogEntry) =>
      (
        await api.post('/documents', {
          title: entry.name,
          relative_path: entry.relative_path,
          category: entry.root_name.toLowerCase(),
          project_id: projectId,
          folder_id: selectedFolderId,
        })
      ).data,
    onSuccess: invalidateDocuments,
  })

  const deleteDocumentMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      if (selectedDocumentId !== null) onSelectDocument(null)
      invalidateDocuments()
    },
  })

  const onSubmitFolder = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!newFolderName.trim() || createFolderMutation.isPending) return
    createFolderMutation.mutate({ name: newFolderName.trim(), parent_id: selectedFolderId })
  }

  const onFilePicked = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file) uploadMutation.mutate(file)
  }

  const downloadFile = async (fileId: string, name: string) => {
    const response = await api.get<Blob>(`/files/${fileId}/content`, { responseType: 'blob' })
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = name
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  }

  const roots = useMemo(() => {
    const entries = catalogQuery.data ?? []
    return ['all', ...Array.from(new Set(entries.map((e) => e.root_name))).sort()]
  }, [catalogQuery.data])

  const attachedPaths = new Set(
    (documentsQuery.data ?? []).map((d) => d.relative_path).filter((p): p is string => p !== null),
  )

  const filteredCatalog = (catalogQuery.data ?? []).filter(
    (entry) => rootFilter === 'all' || entry.root_name === rootFilter,
  )

  const folders = foldersQuery.data ?? []
  const documents = documentsQuery.data ?? []
  const content = contentQuery.data
  const currentFolder = folders.find((f) => f.id === selectedFolderId)

  const renderFolder = (folder: FolderOut, depth: number) => (
    <div key={folder.id}>
      <div
        className="doc-tree-item"
        style={{ display: 'flex', alignItems: 'center', gap: 6, paddingLeft: 8 + depth * 14 }}
      >
        <button
          type="button"
          onClick={() => setSelectedFolderId(folder.id)}
          style={{
            flex: 1,
            textAlign: 'left',
            background: 'none',
            border: 'none',
            font: 'inherit',
            color: 'inherit',
            cursor: 'pointer',
            fontWeight: selectedFolderId === folder.id ? 600 : 400,
          }}
        >
          📁 {folder.name}
        </button>
        <button
          className="btn btn-danger-ghost"
          onClick={() => deleteFolderMutation.mutate(folder.id)}
          disabled={deleteFolderMutation.isPending}
          aria-label={`Удалить папку ${folder.name}`}
        >
          ✕
        </button>
      </div>
      {childrenOf(folders, folder.id).map((child) => renderFolder(child, depth + 1))}
    </div>
  )

  return (
    <div
      style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 16, alignItems: 'start' }}
    >
      <aside className="card card-pad">
        <h2 className="card-title">Папки</h2>
        <div className="doc-tree">
          <div
            className={`doc-tree-item${selectedFolderId === null ? ' selected' : ''}`}
            style={{ cursor: 'pointer' }}
            onClick={() => setSelectedFolderId(null)}
          >
            ▦ Все документы проекта
          </div>
          {foldersQuery.isPending && <Spinner />}
          {foldersQuery.isError && <ErrorBanner error={foldersQuery.error} />}
          {childrenOf(folders, null).map((folder) => renderFolder(folder, 0))}
        </div>
        <form onSubmit={onSubmitFolder} style={{ marginTop: 12 }}>
          <input
            className="input"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder={currentFolder ? `Вложенная в «${currentFolder.name}»` : 'Новая папка'}
            maxLength={200}
            aria-label="Название новой папки"
          />
          <button
            className="btn btn-ghost"
            type="submit"
            style={{ marginTop: 8, width: '100%', justifyContent: 'center' }}
            disabled={!newFolderName.trim() || createFolderMutation.isPending}
          >
            Новая папка
          </button>
        </form>
        {createFolderMutation.isError && <ErrorBanner error={createFolderMutation.error} />}
        {deleteFolderMutation.isError && <ErrorBanner error={deleteFolderMutation.error} />}
      </aside>

      <div className="stack">
        <section className="card card-pad">
          <div className="row-between" style={{ marginBottom: 10 }}>
            <h2 className="card-title" style={{ margin: 0 }}>
              {currentFolder ? `Папка: ${currentFolder.name}` : 'Документы проекта'}
            </h2>
            <div className="topbar-actions">
              <input
                ref={fileInputRef}
                type="file"
                hidden
                onChange={onFilePicked}
                aria-label="Загрузить файл"
              />
              <button
                className="btn btn-primary"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? 'Загрузка…' : 'Загрузить файл'}
              </button>
            </div>
          </div>
          {uploadMutation.isError && <ErrorBanner error={uploadMutation.error} />}
          {deleteDocumentMutation.isError && <ErrorBanner error={deleteDocumentMutation.error} />}
          {documentsQuery.isPending ? (
            <Spinner />
          ) : documentsQuery.isError ? (
            <ErrorBanner error={documentsQuery.error} />
          ) : documents.length === 0 ? (
            <EmptyState
              title="Документов нет"
              hint="Загрузите файл или подключите документ из каталога ниже."
            />
          ) : (
            documents.map((doc) => (
              <div key={doc.id} className="list-row" style={{ padding: '9px 4px' }}>
                <div className="list-main">
                  <span className="list-title">{doc.title}</span>
                  <div className="list-meta mono">{doc.relative_path ?? doc.file_id ?? '—'}</div>
                </div>
                <div className="topbar-actions">
                  <Badge tone="neutral">{doc.category}</Badge>
                  {doc.file_id ? (
                    <Badge tone="accent">файл</Badge>
                  ) : (
                    <Badge tone="success">Markdown</Badge>
                  )}
                  <button
                    className="btn btn-ghost"
                    onClick={() => onSelectDocument(doc.id)}
                    disabled={contentQuery.isPending}
                  >
                    Открыть
                  </button>
                  <button
                    className="btn btn-danger-ghost"
                    onClick={() => deleteDocumentMutation.mutate(doc.id)}
                    disabled={deleteDocumentMutation.isPending}
                    aria-label={`Удалить ${doc.title}`}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))
          )}
        </section>

        <div className="grid-2">
          <section className="card card-pad">
            <h2 className="card-title">Каталог репозитория</h2>
            <select
              className="select"
              style={{ maxWidth: 260, marginBottom: 12 }}
              value={rootFilter}
              onChange={(e) => setRootFilter(e.target.value)}
              aria-label="Фильтр по разделу документации"
            >
              {roots.map((root) => (
                <option key={root} value={root}>
                  {root === 'all' ? 'Все разделы' : root}
                </option>
              ))}
            </select>
            <div className="doc-tree" style={{ maxHeight: 360, overflowY: 'auto' }}>
              {filteredCatalog.map((entry) => (
                <div
                  key={entry.relative_path}
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <span className="doc-tree-item" style={{ flex: 1, cursor: 'default' }}>
                    {entry.root_name}/{entry.relative_path.split('/').slice(1).join('/')}{' '}
                    {attachedPaths.has(entry.relative_path) && (
                      <Badge tone="success">подключён</Badge>
                    )}
                  </span>
                  <button
                    className="btn btn-ghost"
                    onClick={() => attachMutation.mutate(entry)}
                    disabled={attachMutation.isPending}
                    aria-label={`Подключить ${entry.name}`}
                  >
                    Подключить
                  </button>
                </div>
              ))}
            </div>
            {attachMutation.isError && <ErrorBanner error={attachMutation.error} />}
          </section>

          <section className="card card-pad">
            <h2 className="card-title">Просмотр</h2>
            {contentQuery.isFetching && <Spinner />}
            {!contentQuery.isFetching &&
              (content === undefined ? (
                <EmptyState title="Документ не выбран" hint="Нажмите «Открыть» на документе." />
              ) : (
                <>
                  <div className="row-between" style={{ marginBottom: 8 }}>
                    <strong>{content.document.title}</strong>
                    {content.is_binary ? (
                      <Badge tone="accent">бинарный</Badge>
                    ) : content.missing ? (
                      <Badge tone="danger">файл отсутствует</Badge>
                    ) : (
                      <Badge tone="success">загружен</Badge>
                    )}
                  </div>
                  {content.is_binary ? (
                    <div className="topbar-actions">
                      <button
                        className="btn btn-primary"
                        onClick={() =>
                          void downloadFile(
                            content.document.file_id as string,
                            content.document.title,
                          )
                        }
                      >
                        Скачать
                      </button>
                      <span className="muted">Файл доступен только для скачивания.</span>
                    </div>
                  ) : (
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {content.content ?? '_Файл недоступен на диске._'}
                      </ReactMarkdown>
                    </div>
                  )}
                </>
              ))}
          </section>
        </div>
      </div>
    </div>
  )
}
