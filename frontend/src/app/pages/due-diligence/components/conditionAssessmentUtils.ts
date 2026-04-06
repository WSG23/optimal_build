import type { ImmediateAction } from '../../site-acquisition/components/condition-assessment/ImmediateActionsGrid'

const ACTION_PRIORITY: ImmediateAction['priority'][] = [
  'critical',
  'high',
  'medium',
  'low',
]

export function buildImmediateActions(actions: string[]): ImmediateAction[] {
  return actions.slice(0, 4).map((action, index) => {
    const [rawTitle, ...detailParts] = action.split(':')
    const title = rawTitle?.trim() || `Action ${index + 1}`
    const description = detailParts.join(':').trim()
    return {
      id: `immediate-action-${index}`,
      title,
      description,
      priority: ACTION_PRIORITY[index] ?? 'low',
    }
  })
}
