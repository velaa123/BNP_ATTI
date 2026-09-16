type Page =
  | 'Dashboard'
  | 'Churn Analysis'
  | 'Sales Forecast'
  | 'Customer Segments'
  | 'Inventory & Demand'

interface SidebarProps {
  activePage: Page
  onPageChange: (page: Page) => void
}

const menuItems: { label: Page; icon: string }[] = [
  { label: 'Dashboard', icon: '⌂' },
  { label: 'Churn Analysis', icon: '↗' },
  { label: 'Sales Forecast', icon: '▥' },
  { label: 'Customer Segments', icon: '◎' },
  { label: 'Inventory & Demand', icon: '◫' },
]

function Sidebar({ activePage, onPageChange }: SidebarProps) {
  return (
    <aside className="flex min-h-[calc(100vh-5rem)] w-64 shrink-0 flex-col border-r border-white/10 bg-slate-950/95 p-4">
      <nav className="space-y-2">
        <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Analytics
        </p>

        {menuItems.map((item) => {
          const isActive = activePage === item.label

          return (
            <button
              key={item.label}
              type="button"
              onClick={() => onPageChange(item.label)}
              className={`group flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-violet-500/20 text-white shadow-lg shadow-cyan-500/5'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span
                className={`flex h-9 w-9 items-center justify-center rounded-lg text-lg transition ${
                  isActive
                    ? 'bg-cyan-400/15 text-cyan-300'
                    : 'bg-white/5 text-slate-400 group-hover:bg-cyan-400/10 group-hover:text-cyan-300'
                }`}
              >
                {item.icon}
              </span>

              <span className="text-sm font-medium">
                {item.label}
              </span>
            </button>
          )
        })}
      </nav>

      <div className="mt-auto rounded-2xl border border-violet-400/10 bg-gradient-to-br from-violet-500/10 to-cyan-500/5 p-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-400/10 text-sm text-violet-300">
            AI
          </span>

          <p className="text-xs font-semibold uppercase tracking-wider text-violet-300">
            AI Insights
          </p>
        </div>

        <p className="mt-3 text-xs leading-5 text-slate-400">
          Monitor customer risk, forecast sales, and optimize inventory with
          data-driven insights.
        </p>

        <div className="mt-4 flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/50" />
          <span className="text-[11px] text-slate-500">
            Analytics engine ready
          </span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar