import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../shared/api'
import type { Envelope, MeOut, SettingOut } from '../shared/types'
import { EmptyState, ErrorBanner, Spinner } from '../shared/ui'

type Scope = 'user' | 'organization' | 'platform'

const SCOPE_LABELS: Record<Scope, string> = {
  user: 'Мои',
  organization: 'Организация',
  platform: 'Платформа',
}

export default function SettingsPage() {
  const meQuery = useQuery<MeOut>({
    queryKey: ['me'],
    queryFn: async () => (await api.get<Envelope<MeOut>>('/auth/me')).data.data,
  })
  const roles = meQuery.data?.roles ?? []
  const isOrgAdmin = roles.includes('org_admin') || roles.includes('platform_admin')
  const isPlatformAdmin = roles.includes('platform_admin')

  const [scope, setScope] = useState<Scope>('user')
  const activeScope: Scope =
    (scope === 'organization' && !isOrgAdmin) || (scope === 'platform' && !isPlatformAdmin)
      ? 'user'
      : scope

  const tabs: Scope[] = ['user']
  if (isOrgAdmin) tabs.push('organization')
  if (isPlatformAdmin) tabs.push('platform')

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Настройки</h1>
          <p className="page-subtitle">
            Ключи и значения настроек. Значение хранится как JSON-строка.
          </p>
        </div>
      </div>

      <div className="tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeScope === tab}
            className={`tab${activeScope === tab ? ' active' : ''}`}
            onClick={() => setScope(tab)}
          >
            {SCOPE_LABELS[tab]}
          </button>
        ))}
      </div>

      <SettingsScopePanel scope={activeScope} />
    </>
  )
}

function SettingsScopePanel({ scope }: { scope: Scope }) {
  const queryClient = useQueryClient()
  const [key, setKey] = useState('')
  const [value, setValue] = useState('')
  const [jsonError, setJsonError] = useState<string | null>(null)

  const settingsQuery = useQuery<SettingOut[]>({
    queryKey: ['settings', scope],
    queryFn: async () =>
      (await api.get<Envelope<SettingOut[]>>('/settings', { params: { scope } })).data.data,
  })

  const upsertMutation = useMutation({
    mutationFn: async () =>
      (await api.put('/settings', { scope, key: key.trim(), value: value.trim() })).data,
    onSuccess: () => {
      setKey('')
      setValue('')
      setJsonError(null)
      void queryClient.invalidateQueries({ queryKey: ['settings', scope] })
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!key.trim() || upsertMutation.isPending) return
    try {
      JSON.parse(value)
      setJsonError(null)
    } catch {
      setJsonError('Значение должно быть валидным JSON (например "текст", 123, true, {"a":1}).')
      return
    }
    upsertMutation.mutate()
  }

  return (
    <div className="grid-2">
      <section className="card">
        <div className="card-pad" style={{ paddingBottom: 0 }}>
          <h2 className="card-title">Текущие значения</h2>
        </div>
        {settingsQuery.isPending && <Spinner />}
        {settingsQuery.isError && <ErrorBanner error={settingsQuery.error} />}
        {!settingsQuery.isPending && !settingsQuery.isError && settingsQuery.data.length === 0 && (
          <EmptyState title="Настроек нет" hint="Добавьте первую пару ключ/значение." />
        )}
        {(settingsQuery.data ?? []).map((setting) => (
          <div key={setting.key} className="list-row">
            <div className="list-main">
              <span className="list-title mono">{setting.key}</span>
              <div className="list-meta mono">{setting.value}</div>
            </div>
            <button
              className="btn btn-ghost"
              onClick={() => {
                setKey(setting.key)
                setValue(setting.value)
              }}
            >
              Изменить
            </button>
          </div>
        ))}
      </section>

      <section className="card card-pad">
        <h2 className="card-title">Добавить / изменить</h2>
        <form onSubmit={onSubmit}>
          <label className="field-label" htmlFor="setting-key">
            Ключ
          </label>
          <input
            id="setting-key"
            className="input mono"
            value={key}
            maxLength={100}
            placeholder="например theme"
            onChange={(e) => setKey(e.target.value)}
          />
          <label className="field-label" htmlFor="setting-value" style={{ marginTop: 12 }}>
            Значение (JSON)
          </label>
          <textarea
            id="setting-value"
            className="textarea mono"
            rows={3}
            value={value}
            placeholder='"dark"'
            onChange={(e) => setValue(e.target.value)}
          />
          {jsonError && <div className="error-banner">{jsonError}</div>}
          {upsertMutation.isError && <ErrorBanner error={upsertMutation.error} />}
          <button
            className="btn btn-primary"
            type="submit"
            style={{ marginTop: 12 }}
            disabled={!key.trim() || upsertMutation.isPending}
          >
            {upsertMutation.isPending ? 'Сохранение…' : 'Сохранить'}
          </button>
        </form>
      </section>
    </div>
  )
}
