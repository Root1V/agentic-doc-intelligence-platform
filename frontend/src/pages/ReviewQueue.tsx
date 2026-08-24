import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useReviewQueue, useSubmitCorrection } from '@/lib/queries'
import { humanizeFieldName } from '@/lib/extraction'
import { canExecute } from '@/lib/auth'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { ReviewItem } from '@/types/api'

const REASON_LABEL: Record<string, string> = {
  low_confidence: 'Confianza baja',
  validation_issue: 'Problema de validación',
}

function ReviewRow({ item }: { item: ReviewItem }) {
  const submitCorrection = useSubmitCorrection()
  const [correcting, setCorrecting] = useState(false)
  const [value, setValue] = useState(String(item.current_value.value ?? ''))
  const canCorrect = canExecute()

  function handleSubmit() {
    submitCorrection.mutate(
      { reviewItemId: item.id, body: { corrected_value: value } },
      {
        onSuccess: () => toast.success('Corrección guardada.'),
        onError: () => toast.error('No se pudo guardar la corrección.'),
      },
    )
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/documents/${item.document_id}`} className="text-sm font-medium hover:underline">
            {humanizeFieldName(item.field_path)}
          </Link>
          <Badge variant="outline" className="text-xs">
            {REASON_LABEL[item.reason] ?? item.reason}
          </Badge>
          <Badge variant="outline" className="text-xs">
            confianza {(item.confidence * 100).toFixed(0)}%
          </Badge>
        </div>

        {!correcting ? (
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm text-muted-foreground">Valor actual: {String(item.current_value.value ?? '—')}</span>
            {canCorrect && (
              <Button size="sm" variant="outline" onClick={() => setCorrecting(true)}>
                Corregir
              </Button>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Input value={value} onChange={(e) => setValue(e.target.value)} className="max-w-sm" />
            <Button size="sm" disabled={submitCorrection.isPending} onClick={handleSubmit}>
              {submitCorrection.isPending && <Loader2 className="size-3.5 animate-spin" />}
              Guardar
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setCorrecting(false)}>
              Cancelar
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function ReviewQueuePage() {
  const { data: items, isLoading } = useReviewQueue()

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Cola de revisión</h1>
        <p className="text-muted-foreground">Campos con baja confianza o con observaciones de validación.</p>
      </div>

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : !items || items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No hay elementos pendientes de revisión.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <ReviewRow key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
