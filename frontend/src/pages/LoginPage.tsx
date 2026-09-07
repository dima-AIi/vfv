import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { api } from '../shared/api'
import { setTokens } from '../shared/auth'
import type { AuthTokens, AuthUser, Envelope } from '../shared/types'
import { ErrorBanner } from '../shared/ui'

interface LoginResponse {
  user: AuthUser
  tokens: AuthTokens
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const loginMutation = useMutation({
    mutationFn: async (payload: { email: string; password: string }) =>
      (await api.post<Envelope<LoginResponse>>('/auth/login', payload)).data.data,
    onSuccess: (data) => {
      setTokens(data.tokens.access_token, data.tokens.refresh_token)
      const from = (location.state as { from?: string } | null)?.from ?? '/'
      navigate(from, { replace: true })
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!email.trim() || !password || loginMutation.isPending) return
    loginMutation.mutate({ email: email.trim(), password })
  }

  return (
    <div style={{ maxWidth: 420, margin: '64px auto' }}>
      <div className="card card-pad">
        <h1 className="page-title">Вход в DevOS</h1>
        <p className="page-subtitle" style={{ marginBottom: 16 }}>
          Введите данные учётной записи.
        </p>
        <form onSubmit={onSubmit}>
          <label className="field-label" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            className="input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            autoComplete="email"
          />
          <label className="field-label" htmlFor="login-password" style={{ marginTop: 12 }}>
            Пароль
          </label>
          <input
            id="login-password"
            className="input"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          {loginMutation.isError && <ErrorBanner error={loginMutation.error} />}
          <button
            className="btn btn-primary"
            type="submit"
            disabled={!email.trim() || !password || loginMutation.isPending}
            style={{ marginTop: 16, width: '100%', justifyContent: 'center' }}
          >
            {loginMutation.isPending ? 'Вход…' : 'Войти'}
          </button>
        </form>
        <p className="muted" style={{ marginTop: 14, marginBottom: 0 }}>
          Нет учётной записи? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </div>
    </div>
  )
}
