import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

// Mirrors the real stage transitions orchestrator.py now persists (and
// commits immediately, not batched) so a document polled mid-pipeline shows
// which step it's actually on instead of jumping straight from "uploaded"
// to "extracted" once everything finishes.
const STAGE_COUNT = 6
const STAGE_INDEX: Record<string, number> = {
  uploaded: 0,
  parsing: 1,
  classifying: 2,
  extracting: 3,
  extracted: 4,
  validating: 4,
}

const STAGE_LABEL: Record<string, string> = {
  uploaded: 'En cola',
  parsing: 'Analizando documento',
  classifying: 'Clasificando tipo',
  extracting: 'Extrayendo campos',
  extracted: 'Validando',
  validating: 'Validando',
}

/** Only meaningful for in-progress statuses — a terminal document (completed
 * | needs_review | failed) already gets its own badge elsewhere. */
export function isPipelineInProgress(status: string): boolean {
  return status in STAGE_INDEX
}

export function PipelineStepper({ status }: { status: string }) {
  const filled = (STAGE_INDEX[status] ?? 0) + 1

  return (
    <div className="flex w-full flex-col gap-1">
      <div className="flex gap-0.5">
        {Array.from({ length: STAGE_COUNT }, (_, i) => (
          <div key={i} className={cn('h-1 flex-1 rounded-full', i < filled ? 'bg-primary' : 'bg-muted')} />
        ))}
      </div>
      <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
        <Loader2 className="size-2.5 animate-spin" />
        {STAGE_LABEL[status] ?? status}
      </span>
    </div>
  )
}
