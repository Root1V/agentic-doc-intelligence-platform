// The dedicated document browser — the dashboard's "recent documents" list
// caps at a handful of rows and has no filter controls; this page is the
// real way to work the full corpus (already 100+ documents) by status,
// type, or needs_review. No new backend work: GET /documents already
// supports these filters, this page is the first UI that actually uses
// them combined.
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, FileText, Loader2 } from 'lucide-react'
import { useDocumentList, useDocumentTypeCatalog } from '@/lib/queries'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const STATUS_OPTIONS = [
  'uploaded',
  'parsing',
  'classifying',
  'extracting',
  'segmented',
  'extracted',
  'validating',
  'needs_review',
  'completed',
  'failed',
]
const ALL = '__all__'
const PAGE_SIZE = 25

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  completed: 'secondary',
  needs_review: 'destructive',
  failed: 'destructive',
}

export function DocumentsPage() {
  const [status, setStatus] = useState(ALL)
  const [documentType, setDocumentType] = useState(ALL)
  const [needsReview, setNeedsReview] = useState(ALL)
  const [offset, setOffset] = useState(0)

  const { data: catalog } = useDocumentTypeCatalog()
  const { data, isLoading, isFetching } = useDocumentList({
    status: status === ALL ? undefined : status,
    document_type: documentType === ALL ? undefined : documentType,
    needs_review: needsReview === ALL ? undefined : needsReview === 'true',
    limit: PAGE_SIZE,
    offset,
  })

  const documents = useMemo(() => (data?.documents ?? []).filter((doc) => doc.status !== 'segmented'), [data])

  function resetAndSet(setter: (value: string) => void) {
    return (value: string) => {
      setter(value)
      setOffset(0)
    }
  }

  const total = data?.total ?? 0
  const page = Math.floor(offset / PAGE_SIZE) + 1
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Documentos</h1>
        <p className="text-muted-foreground">Explora y filtra todos los documentos procesados ({total} en total).</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Select value={status} onValueChange={resetAndSet(setStatus)}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Todos los estados</SelectItem>
            {STATUS_OPTIONS.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={documentType} onValueChange={resetAndSet(setDocumentType)}>
          <SelectTrigger className="w-56">
            <SelectValue placeholder="Tipo de documento" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Todos los tipos</SelectItem>
            <SelectItem value="generic">generic</SelectItem>
            {catalog?.registered.map((type) => (
              <SelectItem key={type.name} value={type.name}>
                {type.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={needsReview} onValueChange={resetAndSet(setNeedsReview)}>
          <SelectTrigger className="w-52">
            <SelectValue placeholder="Revisión" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Todos</SelectItem>
            <SelectItem value="true">Requieren revisión</SelectItem>
            <SelectItem value="false">No requieren revisión</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Documento</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Confianza</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Revisión</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-sm text-muted-foreground">
                      Sin documentos que coincidan con los filtros.
                    </TableCell>
                  </TableRow>
                ) : (
                  documents.map((doc) => (
                    <TableRow key={doc.id} className={isFetching ? 'opacity-60' : undefined}>
                      <TableCell>
                        <Link to={`/documents/${doc.id}`} className="flex items-center gap-2 hover:underline">
                          <FileText className="size-4 shrink-0 text-muted-foreground" />
                          <span className="truncate">{doc.original_filename}</span>
                        </Link>
                      </TableCell>
                      <TableCell>
                        {doc.document_type ? (
                          <Badge variant="outline" className="text-[10px]">
                            {doc.document_type}
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {doc.classification_confidence !== null ? (
                          <span className="text-xs">{(doc.classification_confidence * 100).toFixed(0)}%</span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANT[doc.status] ?? 'secondary'} className="text-[10px]">
                          {doc.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{doc.needs_review && <Badge variant="destructive">Requiere revisión</Badge>}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Página {page} de {totalPages}
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="icon" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
                <ChevronLeft className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
