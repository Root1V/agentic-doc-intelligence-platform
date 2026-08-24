import { Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { useResolveTypeSuggestion, useTypeSuggestions } from '@/lib/queries'
import { canExecute } from '@/lib/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export function TypeSuggestionsPage() {
  const { data: suggestions, isLoading } = useTypeSuggestions()
  const resolve = useResolveTypeSuggestion()
  const canResolve = canExecute()

  function handle(suggestionId: string, decision: 'accept' | 'reject') {
    resolve.mutate(
      { suggestionId, decision },
      {
        onSuccess: () => toast.success(decision === 'accept' ? 'Sugerencia aceptada.' : 'Sugerencia rechazada.'),
        onError: () => toast.error('No se pudo procesar la decisión.'),
      },
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Sugerencias de tipo</h1>
        <p className="text-muted-foreground">
          Cuando un documento cae en <code>generic</code>, el sistema puede proponer un tipo nuevo. Aceptar solo marca la
          propuesta como accionable — no registra el tipo automáticamente, eso sigue siendo un cambio de código.
        </p>
      </div>

      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : !suggestions || suggestions.length === 0 ? (
        <p className="text-sm text-muted-foreground">No hay sugerencias pendientes.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {suggestions.map((suggestion) => (
            <Card key={suggestion.id}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sparkles className="size-4 text-primary" />
                  <CardTitle>{suggestion.suggested_display_name}</CardTitle>
                  <Badge variant="outline" className="font-mono text-xs">
                    {suggestion.suggested_type_name}
                  </Badge>
                </div>
                <CardDescription>{suggestion.rationale}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div className="overflow-x-auto rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Campo</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead>Requerido</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {suggestion.fields.map((field) => (
                        <TableRow key={field.name}>
                          <TableCell className="font-mono text-xs">{field.name}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{field.field_type}</TableCell>
                          <TableCell className="text-xs">{field.description}</TableCell>
                          <TableCell>{field.required ? 'Sí' : 'No'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                {canResolve && (
                  <div className="flex gap-2">
                    <Button size="sm" disabled={resolve.isPending} onClick={() => handle(suggestion.id, 'accept')}>
                      Aceptar
                    </Button>
                    <Button size="sm" variant="outline" disabled={resolve.isPending} onClick={() => handle(suggestion.id, 'reject')}>
                      Rechazar
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
