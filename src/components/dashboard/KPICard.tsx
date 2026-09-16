interface KPICardProps {
  title: string
  value: string
  change?: string
  description?: string
  icon: string
  trend?: 'up' | 'down' | 'neutral'
}

function KPICard({
  title,
  value,
  change,
  description,
  icon,
  trend = 'neutral',
}: KPICardProps) {
  const trendStyles = {
    up: 'text-emerald-400 bg-emerald-400/10',
    down: 'text-red-400 bg-red-400/10',
    neutral: 'text-slate-400 bg-slate-400/10',
  }

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:border-cyan-400/20 hover:bg-white/[0.05]">
      {/* Glow */}
      <div className="absolute -right-10 -top-10 h-24 w-24 rounded-full bg-cyan-400/10 blur-3xl transition group-hover:bg-cyan-400/20" />

      <div className="relative">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-400">
              {title}
            </p>

            <h3 className="mt-2 text-2xl font-bold tracking-tight text-white">
              {value}
            </h3>
          </div>

          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400/15 to-violet-500/15 text-xl ring-1 ring-white/5">
            {icon}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-4 flex items-center gap-2">
          {change && (
            <span
              className={`rounded-full px-2 py-1 text-xs font-semibold ${trendStyles[trend]}`}
            >
              {change}
            </span>
          )}

          {description && (
            <span className="text-xs text-slate-500">
              {description}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default KPICard