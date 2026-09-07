import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../shared/api'
import { ROLE_LABELS, USER_STATUS_LABELS, formatLabel } from '../shared/labels'
import type { Envelope, InvitedUser, MeOut, UserRow } from '../shared/types'
import { Badge, EmptyState, ErrorBanner, Spinner } from '../shared/ui'

const ASSIGNABLE_ROLES = ['org_admin', 'manager', 'employee']

export default function UsersPage() {
  const queryClient = useQueryClient()
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteName, setInviteName] = useState('')
  const [invited, setInvited] = useState<InvitedUser | null>(null)

  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
  })
  const orgId = meQuery.data?.organization_id ?? null

  const usersQuery = useQuery<UserRow[]>({
    queryKey: ['org-users', orgId],
    queryFn: async () =>
      (
        await api.get<Envelope<UserRow[]>>(`/organizations/${orgId}/users`, {
          params: { pageSize: 100 },
        })
      ).data.data,
    enabled: Boolean(orgId),
  })

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ['org-users', orgId] })

  const inviteMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<Envelope<InvitedUser>>(`/organizations/${orgId}/users`, {
          email: inviteEmail.trim(),
          displayName: inviteName.trim(),
        })
      ).data.data,
    onSuccess: (data) => {
      setInviteEmail('')
      setInviteName('')
      setInvited(data)
      invalidate()
    },
  })

  const roleMutation = useMutation({
    mutationFn: async (payload: { userId: string; role: string }) =>
      api.patch(`/organizations/${orgId}/users/${payload.userId}/role`, { role: payload.role }),
    onSuccess: invalidate,
  })

  const statusMutation = useMutation({
    mutationFn: async (payload: { userId: string; status: string }) =>
      api.patch(`/organizations/${orgId}/users/${payload.userId}/status`, {
        status: payload.status,
      }),
    onSuccess: invalidate,
  })

  const onInvite = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!inviteEmail.trim() || !inviteName.trim() || inviteMutation.isPending) return
    inviteMutation.mutate()
  }

  if (!orgId) return <EmptyState title="Нет организации" hint="Создайте организацию сначала." />
  if (usersQuery.isPending) return <Spinner />
  if (usersQuery.isError) return <ErrorBanner error={usersQuery.error} />

  const users = usersQuery.data

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Пользователи</h1>
          <p className="page-subtitle">Участники организации: приглашение, роли, блокировка.</p>
        </div>
      </div>

      {roleMutation.isError && <ErrorBanner error={roleMutation.error} />}
      {statusMutation.isError && <ErrorBanner error={statusMutation.error} />}

      <section className="card">
        {users.map((user) => (
          <div key={user.id} className="list-row">
            <div className="list-main">
              <span className="list-title">{user.display_name}</span>
              <div className="list-meta mono">{user.email}</div>
            </div>
            <div className="topbar-actions">
              <span className="muted" style={{ minWidth: 90 }}>
                Роль: {user.roles.map((role) => formatLabel(ROLE_LABELS, role)).join(', ') || '—'}
              </span>
              <select
                className="select"
                style={{ width: 150 }}
                aria-label={`Роль ${user.display_name}`}
                defaultValue={user.roles.find((role) => ASSIGNABLE_ROLES.includes(role)) ?? ''}
                key={`role-${user.id}-${user.roles.join(',')}`}
                onChange={(e) =>
                  e.target.value && roleMutation.mutate({ userId: user.id, role: e.target.value })
                }
              >
                <option value="">сменить роль…</option>
                {ASSIGNABLE_ROLES.map((role) => (
                  <option key={role} value={role}>
                    {formatLabel(ROLE_LABELS, role)}
                  </option>
                ))}
              </select>
              <Badge tone={user.status === 'active' ? 'success' : 'danger'}>
                {formatLabel(USER_STATUS_LABELS, user.status)}
              </Badge>
              {user.status === 'active' ? (
                <button
                  className="btn btn-danger-ghost"
                  onClick={() => {
                    if (window.confirm(`Заблокировать ${user.display_name}?`)) {
                      statusMutation.mutate({ userId: user.id, status: 'blocked' })
                    }
                  }}
                  disabled={statusMutation.isPending}
                >
                  Заблокировать
                </button>
              ) : (
                <button
                  className="btn btn-ghost"
                  onClick={() => statusMutation.mutate({ userId: user.id, status: 'active' })}
                  disabled={statusMutation.isPending}
                >
                  Разблокировать
                </button>
              )}
            </div>
          </div>
        ))}
      </section>

      <form className="card card-pad" style={{ marginTop: 16 }} onSubmit={onInvite}>
        <h2 className="card-title">Пригласить пользователя</h2>
        <div className="form-row">
          <div style={{ flex: '1 1 200px' }}>
            <label className="field-label" htmlFor="invite-name">
              Имя
            </label>
            <input
              id="invite-name"
              className="input"
              value={inviteName}
              maxLength={200}
              onChange={(e) => setInviteName(e.target.value)}
            />
          </div>
          <div style={{ flex: '2 1 240px' }}>
            <label className="field-label" htmlFor="invite-email">
              Email
            </label>
            <input
              id="invite-email"
              className="input"
              type="email"
              value={inviteEmail}
              maxLength={254}
              onChange={(e) => setInviteEmail(e.target.value)}
            />
          </div>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={!inviteEmail.trim() || !inviteName.trim() || inviteMutation.isPending}
          >
            {inviteMutation.isPending ? 'Приглашение…' : 'Пригласить'}
          </button>
        </div>
        {inviteMutation.isError && <ErrorBanner error={inviteMutation.error} />}
      </form>

      {invited && (
        <>
          <div
            onClick={() => setInvited(null)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(16,24,40,0.4)', zIndex: 40 }}
          />
          <div
            className="card card-pad"
            style={{
              position: 'fixed',
              top: '25%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 440,
              maxWidth: '90vw',
              zIndex: 41,
            }}
          >
            <h2 className="card-title" style={{ marginTop: 0 }}>
              Пользователь приглашён
            </h2>
            <p className="muted">Скопируйте временный пароль — он показывается только один раз.</p>
            <div className="card card-pad" style={{ background: 'var(--bg)' }}>
              <span className="mono" style={{ fontSize: 15, wordBreak: 'break-all' }}>
                {invited.generated_password ?? '—'}
              </span>
            </div>
            <div className="topbar-actions" style={{ marginTop: 14, justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => setInvited(null)}>
                Готово
              </button>
            </div>
          </div>
        </>
      )}
    </>
  )
}
