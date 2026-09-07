import type { AIActionStatus } from '../../shared/types'
import { AI_ACTION_LABELS, AI_STATUS_LABELS, formatLabel } from '../../shared/labels'
import { Badge } from '../../shared/ui'

export function ActionStatusBadge({ status }: { status: AIActionStatus }) {
  if (status === 'completed')
    return <Badge tone="success">{formatLabel(AI_STATUS_LABELS, status)}</Badge>
  if (status === 'failed')
    return <Badge tone="danger">{formatLabel(AI_STATUS_LABELS, status)}</Badge>
  return <Badge tone="warning">{formatLabel(AI_STATUS_LABELS, 'pending')}</Badge>
}

export function ActionTypeBadge({ type }: { type: string }) {
  return <Badge tone="accent">{formatLabel(AI_ACTION_LABELS, type)}</Badge>
}
