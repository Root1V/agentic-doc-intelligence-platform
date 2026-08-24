import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Upload, Files, ClipboardCheck, Sparkles, BookOpen, History, LogOut, FileStack } from 'lucide-react'
import { cn } from '@/lib/utils'
import { clearSession, getUserName } from '@/lib/auth'

const NAV_ITEMS = [
  { to: '/', label: 'Inicio', icon: LayoutDashboard, end: true },
  { to: '/upload', label: 'Subir documentos', icon: Upload },
  { to: '/documents', label: 'Documentos', icon: Files },
  { to: '/review', label: 'Cola de revisión', icon: ClipboardCheck },
  { to: '/type-suggestions', label: 'Sugerencias de tipo', icon: Sparkles },
  { to: '/document-types', label: 'Plantillas', icon: BookOpen },
  { to: '/audit', label: 'Auditoría', icon: History },
]

export function Sidebar() {
  const userName = getUserName()

  return (
    <aside className="flex h-svh w-64 shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <FileStack className="size-5" />
        </div>
        <div>
          <div className="text-sm font-semibold leading-tight">IDP</div>
          <div className="text-xs text-muted-foreground leading-tight">Plataforma Documental</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
              )
            }
          >
            <Icon className="size-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t px-3 py-4">
        <div className="mb-2 px-2 text-sm font-medium">{userName ?? 'Usuario'}</div>
        <button
          type="button"
          onClick={() => {
            clearSession()
            window.location.assign('/login')
          }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/80 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        >
          <LogOut className="size-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
