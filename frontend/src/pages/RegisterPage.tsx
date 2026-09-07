import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'

import { api } from '../shared/api'
import { setTokens } from '../shared/auth'
import type { AuthTokens, AuthUser, Envelope } from '../shared/types'
import { ErrorBanner } from '../shared/ui'

interface LoginResponse {
  user: AuthUser
  tokens: AuthTokens
}

const EMAIL_PATTERN = /\S+@\S+\.\S+/

export default function RegisterPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [validationMessage, setValidationMessage] = useState<string | null>(null)

  const registerMutation = useMutation({
    mutationFn: async (payload: { email: string; password: string; displayName: string }) => {
      await api.post<Envelope<AuthUser>>('/auth/register', payload)
      const login = await api.post<Envelope<LoginResponse>>('/auth/login', {
        email: payload.email,
        password: payload.password,
      })
      return login.data.data
    },
    onSuccess: (data) => {
      setTokens(data.tokens.access_token, data.tokens.refresh_token)
      navigate('/', { replace: true })
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (
      !email.trim() ||
      !displayName.trim() ||
      !password ||
      !confirmPassword ||
      registerMutation.isPending
    ) {
      return
    }
    if (!EMAIL_PATTERN.test(email.trim())) {
      setValidationMessage('Введите корректный email.')
      return
    }
    if (password !== confirmPassword) {
      setValidationMessage('Пароли не совпадают.')
      return
    }
    setValidationMessage(null)
    registerMutation.mutate({
      email: email.trim(),
      password,
      displayName: displayName.trim(),
    })
  }

  return (
    <div style={{ maxWidth: 420, margin: '64px auto' }}>
      <div className="card card-pad">
        <h1 className="page-title">Регистрация</h1>
        <p className="page-subtitle" style={{ marginBottom: 16 }}>
          Создайте учётную запись DevOS.
        </p>
        <form onSubmit={onSubmit}>
          <label className="field-label" htmlFor="register-email">
            Email
          </label>
          <input
            id="register-email"
            className="input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            autoComplete="email"
          />
          <label className="field-label" htmlFor="register-name" style={{ marginTop: 12 }}>
            Отображаемое имя
          </label>
          <input
            id="register-name"
            className="input"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={200}
          />
          <label className="field-label" htmlFor="register-password" style={{ marginTop: 12 }}>
            Пароль (минимум 8 символов)
          </label>
          <input
            id="register-password"
            className="input"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
          <label className="field-label" htmlFor="register-confirm" style={{ marginTop: 12 }}>
            Подтверждение пароля
          </label>
          <input
            id="register-confirm"
            className="input"
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
          />
          {validationMessage && <ErrorBanner error={{ message: validationMessage }} />}
          {registerMutation.isError && <ErrorBanner error={registerMutation.error} />}
          <button
            className="btn btn-primary"
            type="submit"
            disabled={
              !email.trim() ||
              !displayName.trim() ||
              !password ||
              !confirmPassword ||
              registerMutation.isPending
            }
            style={{ marginTop: 16, width: '100%', justifyContent: 'center' }}
          >
            {registerMutation.isPending ? 'Создание…' : 'Зарегистрироваться'}
          </button>
        </form>
        <p className="muted" style={{ marginTop: 14, marginBottom: 0 }}>
          Уже есть учётная запись? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  )
}
