import type { ReactNode } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh w-full bg-background">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden px-8 py-6">{children}</main>
    </div>
  )
}
