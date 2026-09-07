export interface ApiErrorView {
  message: string
  code?: string
}

export function getApiError(error: unknown): ApiErrorView {
  if (error instanceof Object && 'message' in error) {
    const candidate = error as { message?: unknown; code?: unknown }
    return {
      message: typeof candidate.message === 'string' ? candidate.message : 'Ошибка запроса',
      code: typeof candidate.code === 'string' ? candidate.code : undefined,
    }
  }
  return { message: String(error) }
}
