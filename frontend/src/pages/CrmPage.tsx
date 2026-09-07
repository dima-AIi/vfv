import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../shared/api'
import { formatDateTime } from '../shared/datetime'
import { CUSTOMER_STATUS_LABELS, formatLabel } from '../shared/labels'
import type { CompanyOut, CustomerOut, CustomerStatus, Envelope } from '../shared/types'
import { Badge, EmptyState, ErrorBanner, Pager, Spinner } from '../shared/ui'

const PAGE_SIZE = 10

const STATUS_TONES: Record<CustomerStatus, 'neutral' | 'success' | 'warning'> = {
  lead: 'neutral',
  active: 'success',
  archived: 'warning',
}

export default function CrmPage() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<'' | CustomerStatus>('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [companyId, setCompanyId] = useState('')

  const companiesQuery = useQuery<CompanyOut[]>({
    queryKey: ['companies', 'all'],
    queryFn: async () =>
      (await api.get<Envelope<CompanyOut[]>>('/companies', { params: { pageSize: 100 } })).data
        .data,
  })

  const customersQuery = useQuery<Envelope<CustomerOut[]>>({
    queryKey: ['customers', page, status, q],
    queryFn: async () =>
      (
        await api.get<Envelope<CustomerOut[]>>('/customers', {
          params: {
            page,
            pageSize: PAGE_SIZE,
            ...(status ? { status } : {}),
            ...(q.trim() ? { q: q.trim() } : {}),
          },
        })
      ).data,
  })

  const createMutation = useMutation({
    mutationFn: async (payload: { name: string; description: string; company_id?: string }) =>
      (await api.post('/customers', payload)).data,
    onSuccess: () => {
      setName('')
      setDescription('')
      setCompanyId('')
      setCreating(false)
      void queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim() || createMutation.isPending) return
    createMutation.mutate({
      name: name.trim(),
      description: description.trim(),
      ...(companyId ? { company_id: companyId } : {}),
    })
  }

  if (customersQuery.isPending) return <Spinner />
  if (customersQuery.isError) return <ErrorBanner error={customersQuery.error} />

  const envelope = customersQuery.data
  const customers = envelope.data
  const pagination = envelope.meta.pagination

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">CRM</h1>
          <p className="page-subtitle">
            Клиенты, контакты, заметки и теги. Карточка клиента связана с проектами.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setCreating(true)}>
          Создать клиента
        </button>
      </div>

      <div className="card card-pad" style={{ marginBottom: 16 }}>
        <div className="form-row">
          <div style={{ flex: '1 1 180px' }}>
            <label className="field-label" htmlFor="crm-status">
              Статус
            </label>
            <select
              id="crm-status"
              className="select"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value as '' | CustomerStatus)
                setPage(1)
              }}
            >
              <option value="">Все</option>
              <option value="lead">Лид</option>
              <option value="active">Активен</option>
              <option value="archived">В архиве</option>
            </select>
          </div>
          <div style={{ flex: '2 1 260px' }}>
            <label className="field-label" htmlFor="crm-search">
              Поиск
            </label>
            <input
              id="crm-search"
              className="input"
              type="search"
              value={q}
              placeholder="По имени или описанию"
              onChange={(e) => {
                setQ(e.target.value)
                setPage(1)
              }}
            />
          </div>
        </div>
      </div>

      {pagination && pagination.totalItems === 0 ? (
        <div className="card">
          <EmptyState
            title="Клиентов нет"
            hint="Создайте первого клиента — он появится в списке."
          />
        </div>
      ) : (
        <>
          <section className="card">
            {customers.map((customer) => (
              <div key={customer.id} className="list-row">
                <div className="list-main">
                  <Link to={`/crm/${customer.id}`} style={{ textDecoration: 'none' }}>
                    <span className="list-title">{customer.name}</span>
                  </Link>
                  <div className="list-desc">{customer.description || '—'}</div>
                  <div className="list-meta">
                    компания: {customer.company_name ?? '—'} · обновлён{' '}
                    {formatDateTime(customer.updated_at)}
                  </div>
                  {customer.tags.length > 0 && (
                    <div className="topbar-actions" style={{ marginTop: 6, gap: 6 }}>
                      {customer.tags.map((tag) => (
                        <Badge key={tag.id} tone="accent">
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <Badge tone={STATUS_TONES[customer.status]}>
                  {formatLabel(CUSTOMER_STATUS_LABELS, customer.status)}
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

      {creating && (
        <>
          <div
            onClick={() => setCreating(false)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(16,24,40,0.4)', zIndex: 40 }}
          />
          <div
            className="card card-pad"
            style={{
              position: 'fixed',
              top: '20%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 420,
              maxWidth: '90vw',
              zIndex: 41,
            }}
          >
            <h2 className="card-title" style={{ marginTop: 0 }}>
              Новый клиент
            </h2>
            <form onSubmit={onSubmit}>
              <label className="field-label" htmlFor="new-customer-name">
                Название
              </label>
              <input
                id="new-customer-name"
                className="input"
                value={name}
                maxLength={200}
                required
                onChange={(e) => setName(e.target.value)}
              />
              <label className="field-label" htmlFor="new-customer-desc" style={{ marginTop: 12 }}>
                Описание
              </label>
              <textarea
                id="new-customer-desc"
                className="textarea"
                rows={3}
                value={description}
                maxLength={5000}
                onChange={(e) => setDescription(e.target.value)}
              />
              <label
                className="field-label"
                htmlFor="new-customer-company"
                style={{ marginTop: 12 }}
              >
                Компания
              </label>
              <select
                id="new-customer-company"
                className="select"
                value={companyId}
                onChange={(e) => setCompanyId(e.target.value)}
              >
                <option value="">— без компании —</option>
                {(companiesQuery.data ?? []).map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
              {createMutation.isError && <ErrorBanner error={createMutation.error} />}
              <div className="topbar-actions" style={{ marginTop: 14, justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setCreating(false)}>
                  Отмена
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!name.trim() || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Создание…' : 'Создать'}
                </button>
              </div>
            </form>
          </div>
        </>
      )}
    </>
  )
}
