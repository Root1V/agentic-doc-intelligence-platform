import { Link, useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useBatch } from '@/lib/queries'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { DocumentThumbnail } from '@/components/documents/DocumentThumbnail'
import { isPipelineInProgress, PipelineStepper } from '@/components/documents/PipelineStepper'

const STATUS_LABEL: Record<string, string> = {
  uploaded: 'Cargado',
  processing: 'Procesando',
  segmented: 'Segmentado',
  extracted: 'Extraído',
  needs_review: 'Requiere revisión',
  completed: 'Completado',
  failed: 'Falló',
}

export function BatchDetailPage() {
  const { batchId } = useParams<{ batchId: string }>()
  const { data: batch, isLoading } = useBatch(batchId)

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!batch) {
    return <p className="text-muted-foreground">Solicitud no encontrada.</p>
  }

  // "segmented" rows are containers spawned by a physical upload that split
  // into multiple logical documents — no extraction of their own, so only
  // their children (the real documents) are worth showing.
  const documents = batch.documents.filter((doc) => doc.status !== 'segmented')
  const isProcessing = batch.status !== 'completed'

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Solicitud</h1>
        <Badge variant={isProcessing ? 'secondary' : 'default'}>
          {isProcessing && <Loader2 className="size-3 animate-spin" />}
          {STATUS_LABEL[batch.status] ?? batch.status}
        </Badge>
      </div>

      {documents.length === 0 ? (
        <p className="text-sm text-muted-foreground">Procesando documentos...</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {documents.map((doc) => (
            <Link key={doc.id} to={`/documents/${doc.id}`}>
              <Card className="h-full transition-colors hover:border-primary/50">
                <CardContent className="flex flex-col items-center gap-2 p-3">
                  <DocumentThumbnail documentId={doc.id} page={doc.page_start ?? 0} />
                  <div className="flex w-full flex-col items-center gap-1 text-center">
                    <span className="line-clamp-2 text-xs font-medium">{doc.original_filename}</span>
                    {doc.document_type && (
                      <Badge variant="outline" className="text-[10px]">
                        {doc.document_type}
                      </Badge>
                    )}
                    {isPipelineInProgress(doc.status) ? (
                      <PipelineStepper status={doc.status} />
                    ) : (
                      <Badge variant={doc.needs_review ? 'destructive' : 'secondary'} className="text-[10px]">
                        {STATUS_LABEL[doc.status] ?? doc.status}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
