import type { Task, TaskStatus } from '../../shared/types'

export const TASK_STATUS_TONES: Record<TaskStatus, 'success' | 'warning' | 'neutral'> = {
  done: 'success',
  in_progress: 'warning',
  open: 'neutral',
}

function todayIso(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

export function isTaskOverdue(task: Pick<Task, 'due_date' | 'status'>): boolean {
  return task.due_date !== null && task.due_date < todayIso() && task.status !== 'done'
}
