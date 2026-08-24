import { formatValue, humanizeFieldName, isExtractedEnvelope } from '@/lib/extraction'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ConfidenceBadge } from '@/components/documents/ConfidenceBadge'
import type { Extracted } from '@/types/api'
import { cn } from '@/lib/utils'

interface ExtractionTableProps {
  name: string
  rows: Record<string, unknown>[]
  selectedKey: string | null
  onSelect: (envelope: Extracted<unknown>, key: string) => void
}

export function ExtractionTable({ name, rows, selectedKey, onSelect }: ExtractionTableProps) {
  if (rows.length === 0) return null
  const columns = Object.keys(rows[0])

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-muted-foreground">{humanizeFieldName(name)}</h3>
      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col}>{humanizeFieldName(col)}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {columns.map((col) => {
                  const cellValue = row[col]
                  if (!isExtractedEnvelope(cellValue)) {
                    return <TableCell key={col}>{formatValue(cellValue)}</TableCell>
                  }
                  const cellKey = `${name}[${rowIndex}].${col}`
                  const hasLocation = cellValue.page !== null && cellValue.bbox !== null
                  return (
                    <TableCell
                      key={col}
                      onClick={hasLocation ? () => onSelect(cellValue, cellKey) : undefined}
                      className={cn(hasLocation && 'cursor-pointer hover:bg-accent', selectedKey === cellKey && 'bg-accent')}
                    >
                      <div className="flex items-center gap-2 whitespace-nowrap">
                        {formatValue(cellValue.value)}
                        <ConfidenceBadge confidence={cellValue.confidence} />
                      </div>
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
