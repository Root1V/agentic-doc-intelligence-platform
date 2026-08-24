// The core screen's visual proof: renders one PDF page and overlays
// bounding boxes as absolutely-positioned divs, scaled by percentage since
// every bbox in this platform's data is already normalized [0,1] — no
// pixel math needed, the overlay container just has to be the same
// element react-pdf renders the page canvas into.
import { useState } from 'react'
import { Document, Page } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export interface BboxHighlight {
  bbox: [number, number, number, number]
  active?: boolean
}

interface PdfViewerProps {
  fileUrl: string
  page: number
  onPageChange: (page: number) => void
  highlights: BboxHighlight[]
  width?: number
}

export function PdfViewer({ fileUrl, page, onPageChange, highlights, width = 640 }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null)

  return (
    <div className="flex flex-col items-center gap-3">
      <Document
        file={fileUrl}
        onLoadSuccess={({ numPages: n }) => setNumPages(n)}
        loading={
          <div className="flex h-96 items-center justify-center">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        }
      >
        <div className="relative inline-block overflow-hidden rounded-lg border shadow-sm">
          <Page pageNumber={page + 1} width={width} />
          {highlights.map((highlight, index) => {
            const [x1, y1, x2, y2] = highlight.bbox
            return (
              <div
                key={index}
                className={cn(
                  'pointer-events-none absolute rounded-sm border-2 transition-colors',
                  highlight.active ? 'border-primary bg-primary/20' : 'border-amber-500/70 bg-amber-400/10',
                )}
                style={{
                  left: `${x1 * 100}%`,
                  top: `${y1 * 100}%`,
                  width: `${(x2 - x1) * 100}%`,
                  height: `${(y2 - y1) * 100}%`,
                }}
              />
            )
          })}
        </div>
      </Document>

      {numPages !== null && numPages > 1 && (
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" disabled={page <= 0} onClick={() => onPageChange(page - 1)}>
            <ChevronLeft className="size-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {page + 1} de {numPages}
          </span>
          <Button variant="outline" size="icon" disabled={page >= numPages - 1} onClick={() => onPageChange(page + 1)}>
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
