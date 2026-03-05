import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, ShieldAlert, GitBranch,
  FileText, Wifi, ChevronRight, Layers, History, Hexagon, Map, Usb, Zap, Shield,
} from 'lucide-react'

const links = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard',          group: 'Overview' },
  { to: '/map',       icon: Map,             label: 'Global Risk Map',    group: 'Overview' },
  { to: '/analysis',  icon: ShieldAlert,     label: 'Risk Analysis',      group: 'Bitcoin' },
  { to: '/testnet',   icon: Wifi,            label: 'BTC Testnet Scan',   group: 'Bitcoin' },
  { to: '/batch',     icon: Layers,          label: 'Batch Scanner',      group: 'Bitcoin' },
  { to: '/ethereum',  icon: Hexagon,         label: 'Ethereum Scanner',   group: 'Ethereum' },
  { to: '/migration', icon: GitBranch,       label: 'Migration Planner',  group: 'Actions' },
  { to: '/reports',   icon: FileText,        label: 'Compliance Reports', group: 'Actions' },
  { to: '/history',   icon: History,         label: 'Scan History',       group: 'Data' },
  { to: '/hardware_wallet', icon: Usb,             label: 'Hardware Wallet PQC', group: 'Actions' },
  { to: '/ecosystem',       icon: Zap,             label: 'Ecosystem & Auto',   group: 'Actions' },
  { to: '/defense',         icon: Shield,          label: 'Full-Stack Defense', group: 'Actions' },
]

const groups = ['Overview', 'Bitcoin', 'Ethereum', 'Actions', 'Data']

export default function Sidebar() {
  return (
    <aside className="w-64 min-h-screen bg-slate-900 border-r border-slate-700 flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">Q</span>
          </div>
          <div>
            <div className="text-white font-bold text-sm leading-tight">QuantumGuard</div>
            <div className="text-slate-400 text-xs">Labs QMP v0.2</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-4 overflow-y-auto">
        {groups.map(group => {
          const groupLinks = links.filter(l => l.group === group)
          return (
            <div key={group}>
              <div className="px-3 mb-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {group}
              </div>
              <div className="space-y-0.5">
                {groupLinks.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all group ${
                        isActive
                          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`
                    }
                  >
                    <Icon size={16} />
                    <span className="flex-1">{label}</span>
                    <ChevronRight size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </NavLink>
                ))}
              </div>
            </div>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-700">
        <div className="text-xs text-slate-500 text-center">
          Quantum Migration Platform<br />
          <span className="text-cyan-500">● Live Demo</span>
        </div>
      </div>
    </aside>
  )
}
