import type { Extracted } from '@/types/api'
import { formatValue, humanizeFieldName } from '@/lib/extraction'
import { ConfidenceBadge } from '@/components/documents/ConfidenceBadge'
import { cn } from '@/lib/utils'

interface ExtractionFieldProps {
  name: string
  envelope: Extracted<unknown>
  isSelected: boolean
  onSelect: () => void
}

export function ExtractionField({ name, envelope, isSelected, onSelect }: ExtractionFieldProps) {
  const hasLocation = envelope.page !== null && envelope.bbox !== null

  return (
    <button
      type="button"
      disabled={!hasLocation}
      onClick={onSelect}
      title={envelope.source_text ?? undefined}
      className={cn(
        'flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left transition-colors',
        hasLocation ? 'cursor-pointer hover:border-primary/50' : 'cursor-default opacity-70',
        isSelected && 'border-primary bg-accent',
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-muted-foreground">{humanizeFieldName(name)}</span>
        <ConfidenceBadge confidence={envelope.confidence} />
      </div>
      <span className="text-sm">{formatValue(envelope.value)}</span>
    </button>
  )
}
