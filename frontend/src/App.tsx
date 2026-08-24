import { Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { LoginPage } from '@/pages/Login'
import { DashboardPage } from '@/pages/Dashboard'
import { UploadPage } from '@/pages/Upload'
import { BatchDetailPage } from '@/pages/BatchDetail'
import { DocumentDetailPage } from '@/pages/DocumentDetail'
import { ReviewQueuePage } from '@/pages/ReviewQueue'
import { TypeSuggestionsPage } from '@/pages/TypeSuggestions'
import { DocumentTypesPage } from '@/pages/DocumentTypes'
import { AuditPage } from '@/pages/Audit'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <UploadPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/batches/:batchId"
        element={
          <ProtectedRoute>
            <BatchDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents/:documentId"
        element={
          <ProtectedRoute>
            <DocumentDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/review"
        element={
          <ProtectedRoute>
            <ReviewQueuePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/type-suggestions"
        element={
          <ProtectedRoute>
            <TypeSuggestionsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/document-types"
        element={
          <ProtectedRoute>
            <DocumentTypesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit"
        element={
          <ProtectedRoute>
            <AuditPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
