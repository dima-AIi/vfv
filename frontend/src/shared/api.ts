import axios from 'axios'

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './auth'
import { queryClient } from './queryClient'

export class ApiError extends Error {
  readonly status?: number
  readonly code?: string
  readonly details?: unknown
  readonly requestId?: string

  constructor(
    message: string,
    options: {
      status?: number
      code?: string
      details?: unknown
      requestId?: string
    } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
    this.details = options.details
    this.requestId = options.requestId
  }
}

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

const AUTH_FREE_PATHS = ['/auth/login', '/auth/register', '/auth/refresh']

let refreshInFlight: Promise<string | null> | null = null

async function performRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null
  try {
    const response = await axios.post('/api/v1/auth/refresh', {
      refreshToken,
    })
    const tokens = response.data.data.tokens as {
      access_token: string
      refresh_token: string
    }
    setTokens(tokens.access_token, tokens.refresh_token)
    return tokens.access_token
  } catch {
    clearTokens()
    return null
  }
}

function redirectToLogin(): void {
  queryClient.clear()
  if (!window.location.pathname.startsWith('/login')) {
    window.location.assign('/login')
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error?.config ?? {}
    const status: number | undefined = error?.response?.status
    const url: string = original.url ?? ''
    const isAuthFreePath = AUTH_FREE_PATHS.some((path) => url.startsWith(path))

    if (status === 401 && !isAuthFreePath && !original._retry) {
      original._retry = true
      if (refreshInFlight === null) {
        refreshInFlight = performRefresh().finally(() => {
          refreshInFlight = null
        })
      }
      const newAccessToken = await refreshInFlight
      if (newAccessToken) {
        original.headers = { ...(original.headers ?? {}) }
        original.headers.Authorization = `Bearer ${newAccessToken}`
        return api(original)
      }
      redirectToLogin()
    }

    const body = error?.response?.data?.error
    const message: string = body?.message ?? error.message ?? 'Непредвиденная сетевая ошибка'
    return Promise.reject(
      new ApiError(message, {
        status: error?.response?.status,
        code: body?.code,
        details: body?.details,
        requestId: body?.requestId,
      }),
    )
  },
)
