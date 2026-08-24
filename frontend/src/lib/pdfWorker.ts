// Configures pdf.js's worker once, app-wide. Bundled via Vite's `?url`
// import (not a CDN) so the PDF viewer works offline / without depending
// on a third-party host being reachable.
import { pdfjs } from 'react-pdf'
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc
