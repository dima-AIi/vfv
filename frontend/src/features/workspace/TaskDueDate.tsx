import type { Task } from '../../shared/types'
import { formatDate } from '../../shared/datetime'
import { isTaskOverdue } from './taskMeta'

export default function TaskDueDate({ task }: { task: Task }) {
  if (task.due_date === null) {
    return <span className="muted">—</span>
  }
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span className="mono muted">{formatDate(task.due_date)}</span>
      {isTaskOverdue(task) && <span className="badge badge-overdue">просрочено</span>}
    </span>
  )
}
