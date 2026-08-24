import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuditLog } from '@/lib/queries'
import { humanizeFieldName, formatValue } from '@/lib/extraction'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Card, CardContent } from '@/components/ui/card'

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' })
}

export function AuditPage() {
  const { data, isLoading } = useAuditLog({ limit: 100 })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Auditoría</h1>
        <p className="text-muted-foreground">Historial completo de correcciones hechas desde la cola de revisión.</p>
      </div>

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : !data || data.entries.length === 0 ? (
        <p className="text-sm text-muted-foreground">Aún no se ha corregido ningún campo.</p>
      ) : (
        <Card>
          <CardContent className="overflow-x-auto p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Documento</TableHead>
                  <TableHead>Campo</TableHead>
                  <TableHead>Valor original</TableHead>
                  <TableHead>Valor corregido</TableHead>
                  <TableHead>Revisor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {formatTimestamp(entry.timestamp)}
                    </TableCell>
                    <TableCell>
                      <Link to={`/documents/${entry.document_id}`} className="text-primary hover:underline">
                        Ver documento
                      </Link>
                    </TableCell>
                    <TableCell className="text-xs">{humanizeFieldName(entry.field_path)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground line-through decoration-red-400">
                      {formatValue(entry.original_value.value)}
                    </TableCell>
                    <TableCell className="text-xs font-medium">{formatValue(entry.corrected_value.value)}</TableCell>
                    <TableCell className="text-xs">{entry.reviewer_identity}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
