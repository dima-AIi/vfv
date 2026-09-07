import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../shared/api'
import { formatDateTime } from '../shared/datetime'
import { CUSTOMER_STATUS_LABELS, PROJECT_STATUS_LABELS, formatLabel } from '../shared/labels'
import type {
  CompanyOut,
  ContactOut,
  CustomerNoteOut,
  CustomerOut,
  CustomerStatus,
  Envelope,
  MeOut,
  Project,
  TagOut,
} from '../shared/types'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../shared/ui'

const STATUS_TONES: Record<CustomerStatus, 'neutral' | 'success' | 'warning'> = {
  lead: 'neutral',
  active: 'success',
  archived: 'warning',
}

const TABS = [
  { key: 'overview', label: 'Обзор' },
  { key: 'contacts', label: 'Контакты' },
  { key: 'notes', label: 'Заметки' },
  { key: 'tags', label: 'Теги' },
] as const

type TabKey = (typeof TABS)[number]['key']

function isTabKey(value: string | null): value is TabKey {
  return TABS.some((tab) => tab.key === value)
}

export default function CustomerDetailPage() {
  const { customerId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const activeTab: TabKey = isTabKey(requestedTab) ? requestedTab : 'overview'

  const customerQuery = useQuery<CustomerOut>({
    queryKey: ['customer', customerId],
    queryFn: async () =>
      (await api.get<Envelope<CustomerOut>>(`/customers/${customerId}`)).data.data,
    enabled: Boolean(customerId),
  })

  if (!customerId) return <ErrorBanner error="Отсутствует идентификатор клиента." />
  if (customerQuery.isPending) return <Spinner />
  if (customerQuery.isError) return <ErrorBanner error={customerQuery.error} />

  const customer = customerQuery.data

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">{customer.name}</h1>
          <p className="page-subtitle">{customer.description || 'Описание не задано.'}</p>
        </div>
        <div className="topbar-actions">
          <Badge tone={STATUS_TONES[customer.status]}>
            {formatLabel(CUSTOMER_STATUS_LABELS, customer.status)}
          </Badge>
          {customer.status !== 'archived' ? (
            <ArchiveButton customerId={customerId} action="archive" label="В архив" />
          ) : (
            <ArchiveButton customerId={customerId} action="restore" label="Восстановить" />
          )}
        </div>
      </div>

      <EditCustomerForm customer={customer} />

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

      {activeTab === 'overview' && <OverviewPanel customer={customer} />}
      {activeTab === 'contacts' && <ContactsPanel customerId={customerId} />}
      {activeTab === 'notes' && <NotesPanel customerId={customerId} />}
      {activeTab === 'tags' && <TagsPanel customer={customer} />}
    </>
  )
}

function ArchiveButton({
  customerId,
  action,
  label,
}: {
  customerId: string
  action: 'archive' | 'restore'
  label: string
}) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: async () => api.post(`/customers/${customerId}/${action}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['customer', customerId] })
      void queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
  })
  return (
    <>
      <button
        className="btn btn-ghost"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
      >
        {mutation.isPending ? '…' : label}
      </button>
      {mutation.isError && <ErrorBanner error={mutation.error} />}
    </>
  )
}

function EditCustomerForm({ customer }: { customer: CustomerOut }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState(customer.name)
  const [description, setDescription] = useState(customer.description)
  const dirty = name !== customer.name || description !== customer.description

  const mutation = useMutation({
    mutationFn: async () =>
      (
        await api.patch(`/customers/${customer.id}`, {
          name: name.trim(),
          description: description.trim(),
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['customer', customer.id] })
      void queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim() || mutation.isPending) return
    mutation.mutate()
  }

  return (
    <form className="card card-pad" style={{ marginBottom: 16 }} onSubmit={onSubmit}>
      <div className="form-row">
        <div style={{ flex: '2 1 240px' }}>
          <label className="field-label" htmlFor="edit-name">
            Название
          </label>
          <input
            id="edit-name"
            className="input"
            value={name}
            maxLength={200}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div style={{ flex: '3 1 320px' }}>
          <label className="field-label" htmlFor="edit-desc">
            Описание
          </label>
          <input
            id="edit-desc"
            className="input"
            value={description}
            maxLength={5000}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <button className="btn btn-primary" type="submit" disabled={!dirty || !name.trim()}>
          Сохранить
        </button>
      </div>
      {mutation.isError && <ErrorBanner error={mutation.error} />}
    </form>
  )
}

function OverviewPanel({ customer }: { customer: CustomerOut }) {
  const queryClient = useQueryClient()

  const projectsQuery = useQuery<Project[]>({
    queryKey: ['projects', 'customer', customer.id],
    queryFn: async () =>
      (
        await api.get<Envelope<Project[]>>('/projects', {
          params: { customer_id: customer.id, pageSize: 50 },
        })
      ).data.data,
  })

  const companiesQuery = useQuery<CompanyOut[]>({
    queryKey: ['companies', 'all'],
    queryFn: async () =>
      (await api.get<Envelope<CompanyOut[]>>('/companies', { params: { pageSize: 100 } })).data
        .data,
  })

  const companyMutation = useMutation({
    mutationFn: async (companyId: string) =>
      (await api.patch(`/customers/${customer.id}`, { company_id: companyId || null })).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['customer', customer.id] })
      void queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
  })

  return (
    <div className="grid-2">
      <section className="card card-pad">
        <h2 className="card-title">Компания</h2>
        <label className="field-label" htmlFor={`company-${customer.id}`}>
          Компания клиента
        </label>
        <select
          id={`company-${customer.id}`}
          className="select"
          defaultValue={customer.company_id ?? ''}
          key={`company-${customer.id}-${customer.company_id ?? ''}`}
          disabled={companyMutation.isPending}
          onChange={(e) => companyMutation.mutate(e.target.value)}
        >
          <option value="">— без компании —</option>
          {(companiesQuery.data ?? []).map((company) => (
            <option key={company.id} value={company.id}>
              {company.name}
            </option>
          ))}
        </select>
        {companyMutation.isError && <ErrorBanner error={companyMutation.error} />}
      </section>
      <section className="card">
        <div className="card-pad" style={{ paddingBottom: 0 }}>
          <h2 className="card-title">Связанные проекты</h2>
        </div>
        {projectsQuery.isPending && <Spinner />}
        {projectsQuery.isError && <ErrorBanner error={projectsQuery.error} />}
        {!projectsQuery.isPending && !projectsQuery.isError && projectsQuery.data.length === 0 && (
          <EmptyState title="Проектов нет" hint="Привяжите проект через его карточку." />
        )}
        {(projectsQuery.data ?? []).map((project) => (
          <div key={project.id} className="list-row">
            <div className="list-main">
              <Link to={`/projects/${project.id}`} style={{ textDecoration: 'none' }}>
                <span className="list-title">{project.name}</span>
              </Link>
            </div>
            <Badge tone={project.status === 'active' ? 'success' : 'neutral'}>
              {formatLabel(PROJECT_STATUS_LABELS, project.status)}
            </Badge>
          </div>
        ))}
      </section>
    </div>
  )
}

function ContactsPanel({ customerId }: { customerId: string }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')

  const contactsQuery = useQuery<ContactOut[]>({
    queryKey: ['customer-contacts', customerId],
    queryFn: async () =>
      (await api.get<Envelope<ContactOut[]>>(`/customers/${customerId}/contacts`)).data.data,
  })

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ['customer-contacts', customerId] })

  const addMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post(`/customers/${customerId}/contacts`, {
          name: name.trim(),
          email: email.trim() || null,
          phone: phone.trim() || null,
        })
      ).data,
    onSuccess: () => {
      setName('')
      setEmail('')
      setPhone('')
      invalidate()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/customers/${customerId}/contacts/${id}`),
    onSuccess: invalidate,
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim() || addMutation.isPending) return
    addMutation.mutate()
  }

  return (
    <section className="card card-pad">
      <h2 className="card-title">Контакты</h2>
      {contactsQuery.isPending && <Spinner />}
      {contactsQuery.isError && <ErrorBanner error={contactsQuery.error} />}
      {!contactsQuery.isPending && !contactsQuery.isError && contactsQuery.data.length === 0 && (
        <p className="muted">Контактов нет.</p>
      )}
      {(contactsQuery.data ?? []).map((contact) => (
        <div key={contact.id} className="list-row" style={{ padding: '9px 4px' }}>
          <div className="list-main">
            <span className="list-title">{contact.name}</span>
            <div className="list-meta">
              {contact.email || '—'} · {contact.phone || '—'}
            </div>
          </div>
          <button
            className="btn btn-danger-ghost"
            onClick={() => deleteMutation.mutate(contact.id)}
            disabled={deleteMutation.isPending}
            aria-label={`Удалить контакт ${contact.name}`}
          >
            Удалить
          </button>
        </div>
      ))}
      <form onSubmit={onSubmit} className="form-row" style={{ marginTop: 12 }}>
        <input
          className="input"
          style={{ flex: '1 1 160px' }}
          placeholder="Имя"
          value={name}
          maxLength={200}
          onChange={(e) => setName(e.target.value)}
          aria-label="Имя контакта"
        />
        <input
          className="input"
          style={{ flex: '1 1 180px' }}
          placeholder="Email"
          type="email"
          value={email}
          maxLength={200}
          onChange={(e) => setEmail(e.target.value)}
          aria-label="Email контакта"
        />
        <input
          className="input"
          style={{ flex: '1 1 120px' }}
          placeholder="Телефон"
          value={phone}
          maxLength={50}
          onChange={(e) => setPhone(e.target.value)}
          aria-label="Телефон контакта"
        />
        <button className="btn btn-primary" type="submit" disabled={!name.trim()}>
          Добавить
        </button>
      </form>
      {addMutation.isError && <ErrorBanner error={addMutation.error} />}
      {deleteMutation.isError && <ErrorBanner error={deleteMutation.error} />}
    </section>
  )
}

function NotesPanel({ customerId }: { customerId: string }) {
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
  })

  const notesQuery = useQuery<CustomerNoteOut[]>({
    queryKey: ['customer-notes', customerId],
    queryFn: async () =>
      (await api.get<Envelope<CustomerNoteOut[]>>(`/customers/${customerId}/notes`)).data.data,
  })

  const invalidate = () =>
    void queryClient.invalidateQueries({ queryKey: ['customer-notes', customerId] })

  const addMutation = useMutation({
    mutationFn: async () =>
      (await api.post(`/customers/${customerId}/notes`, { body: body.trim() })).data,
    onSuccess: () => {
      setBody('')
      invalidate()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/customers/${customerId}/notes/${id}`),
    onSuccess: invalidate,
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!body.trim() || addMutation.isPending) return
    addMutation.mutate()
  }

  return (
    <section className="card card-pad">
      <h2 className="card-title">Заметки</h2>
      {notesQuery.isPending && <Spinner />}
      {notesQuery.isError && <ErrorBanner error={notesQuery.error} />}
      {!notesQuery.isPending && !notesQuery.isError && notesQuery.data.length === 0 && (
        <p className="muted">Заметок нет.</p>
      )}
      {(notesQuery.data ?? []).map((note) => (
        <div key={note.id} className="list-row" style={{ padding: '9px 4px' }}>
          <div className="list-main">
            <span className="list-title">{note.author_name ?? '—'}</span>
            <div className="comment-meta">{formatDateTime(note.created_at)}</div>
            <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{note.body}</div>
          </div>
          {meQuery.data && note.author_id === meQuery.data.id && (
            <button
              className="btn btn-danger-ghost"
              onClick={() => deleteMutation.mutate(note.id)}
              disabled={deleteMutation.isPending}
              aria-label="Удалить заметку"
            >
              Удалить
            </button>
          )}
        </div>
      ))}
      <form onSubmit={onSubmit} style={{ marginTop: 12 }}>
        <textarea
          className="textarea"
          rows={2}
          placeholder="Новая заметка…"
          value={body}
          maxLength={5000}
          onChange={(e) => setBody(e.target.value)}
          aria-label="Текст заметки"
        />
        <button
          className="btn btn-primary"
          type="submit"
          style={{ marginTop: 8 }}
          disabled={!body.trim() || addMutation.isPending}
        >
          Добавить заметку
        </button>
      </form>
      {addMutation.isError && <ErrorBanner error={addMutation.error} />}
      {deleteMutation.isError && <ErrorBanner error={deleteMutation.error} />}
    </section>
  )
}

function TagsPanel({ customer }: { customer: CustomerOut }) {
  const queryClient = useQueryClient()
  const [attachTagId, setAttachTagId] = useState('')
  const [newTagName, setNewTagName] = useState('')

  const allTagsQuery = useQuery<TagOut[]>({
    queryKey: ['tags'],
    queryFn: async () => (await api.get<Envelope<TagOut[]>>('/tags')).data.data,
  })

  const invalidateCustomer = () => {
    void queryClient.invalidateQueries({ queryKey: ['customer', customer.id] })
    void queryClient.invalidateQueries({ queryKey: ['customers'] })
    void queryClient.invalidateQueries({ queryKey: ['tags'] })
  }

  const attachMutation = useMutation({
    mutationFn: async (tagId: string) =>
      api.post(`/customers/${customer.id}/tags`, { tagId: tagId }),
    onSuccess: () => {
      setAttachTagId('')
      invalidateCustomer()
    },
  })

  const detachMutation = useMutation({
    mutationFn: async (tagId: string) => api.delete(`/customers/${customer.id}/tags/${tagId}`),
    onSuccess: invalidateCustomer,
  })

  const createTagMutation = useMutation({
    mutationFn: async (tagName: string) => {
      const created = await api.post<Envelope<TagOut>>('/tags', { name: tagName })
      const tagId = created.data.data.id
      await api.post(`/customers/${customer.id}/tags`, { tagId })
      return tagId
    },
    onSuccess: () => {
      setNewTagName('')
      invalidateCustomer()
    },
  })

  const attachedIds = new Set(customer.tags.map((t) => t.id))
  const available = (allTagsQuery.data ?? []).filter((t) => !attachedIds.has(t.id))

  const onCreateTag = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!newTagName.trim() || createTagMutation.isPending) return
    createTagMutation.mutate(newTagName.trim())
  }

  return (
    <section className="card card-pad">
      <h2 className="card-title">Теги</h2>
      {customer.tags.length === 0 ? (
        <p className="muted">Тегов нет.</p>
      ) : (
        <div className="topbar-actions" style={{ flexWrap: 'wrap', gap: 8 }}>
          {customer.tags.map((tag) => (
            <span key={tag.id} className="badge badge-accent" style={{ gap: 6 }}>
              {tag.name}
              <button
                onClick={() => detachMutation.mutate(tag.id)}
                disabled={detachMutation.isPending}
                aria-label={`Открепить ${tag.name}`}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="form-row" style={{ marginTop: 14 }}>
        <div style={{ flex: '2 1 220px' }}>
          <label className="field-label" htmlFor="attach-tag">
            Прикрепить существующий
          </label>
          <select
            id="attach-tag"
            className="select"
            value={attachTagId}
            onChange={(e) => setAttachTagId(e.target.value)}
          >
            <option value="">— выберите тег —</option>
            {available.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </select>
        </div>
        <button
          className="btn btn-ghost"
          style={{ alignSelf: 'flex-end' }}
          disabled={!attachTagId || attachMutation.isPending}
          onClick={() => attachTagId && attachMutation.mutate(attachTagId)}
        >
          Прикрепить
        </button>
      </div>

      <form onSubmit={onCreateTag} className="form-row" style={{ marginTop: 12 }}>
        <input
          className="input"
          style={{ flex: '2 1 220px' }}
          placeholder="Новый тег"
          value={newTagName}
          maxLength={50}
          onChange={(e) => setNewTagName(e.target.value)}
          aria-label="Название нового тега"
        />
        <button
          className="btn btn-primary"
          type="submit"
          disabled={!newTagName.trim() || createTagMutation.isPending}
        >
          Создать и прикрепить
        </button>
      </form>

      {attachMutation.isError && <ErrorBanner error={attachMutation.error} />}
      {detachMutation.isError && <ErrorBanner error={detachMutation.error} />}
      {createTagMutation.isError && <ErrorBanner error={createTagMutation.error} />}
    </section>
  )
}
