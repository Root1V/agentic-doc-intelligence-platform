import { Badge } from '@/components/ui/badge'
import { confidenceLevel } from '@/lib/extraction'
import { cn } from '@/lib/utils'

const LEVEL_CLASSES = {
  high: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400',
  low: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400',
}

export function ConfidenceBadge({ confidence }: { confidence: number }) {
  const level = confidenceLevel(confidence)
  return (
    <Badge variant="outline" className={cn('border-0 text-xs font-medium', LEVEL_CLASSES[level])}>
      {(confidence * 100).toFixed(0)}%
    </Badge>
  )
}
