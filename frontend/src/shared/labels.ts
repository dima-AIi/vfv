export const TASK_STATUS_LABELS: Record<string, string> = {
  open: 'Открыта',
  in_progress: 'В работе',
  done: 'Готово',
}

export const TASK_PRIORITY_LABELS: Record<string, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
}

export const PROJECT_STATUS_LABELS: Record<string, string> = {
  active: 'Активен',
  archived: 'В архиве',
}

export const CUSTOMER_STATUS_LABELS: Record<string, string> = {
  lead: 'Лид',
  active: 'Активен',
  archived: 'В архиве',
}

export const USER_STATUS_LABELS: Record<string, string> = {
  active: 'Активен',
  blocked: 'Заблокирован',
}

export const ROLE_LABELS: Record<string, string> = {
  org_admin: 'Админ организации',
  manager: 'Менеджер',
  employee: 'Сотрудник',
  guest: 'Гость',
  platform_admin: 'Админ платформы',
}

export const AI_ACTION_LABELS: Record<string, string> = {
  analyze: 'Анализ',
  plan: 'План',
  execute: 'Выполнить',
  summarize: 'Сводка',
}

export const AI_STATUS_LABELS: Record<string, string> = {
  pending: 'В очереди',
  completed: 'Выполнено',
  failed: 'Ошибка',
}

export function formatLabel(
  dictionary: Record<string, string>,
  value: string | null | undefined,
  fallback = value ?? '—',
): string {
  if (!value) return fallback
  return dictionary[value] ?? value
}
