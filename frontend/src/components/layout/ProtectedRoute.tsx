import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { isAuthenticated } from '@/lib/auth'
import { AppShell } from '@/components/layout/AppShell'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <AppShell>{children}</AppShell>
}
