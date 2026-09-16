function Navbar() {
  return (
    <header className="flex h-20 items-center justify-between border-b border-white/10 bg-slate-950/80 px-6 backdrop-blur-xl">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-violet-600 shadow-lg shadow-cyan-500/20">
          <span className="text-lg font-black text-white">AI</span>
        </div>

        <div>
          <h1 className="text-lg font-bold tracking-tight text-white">
            Customer Intelligence
          </h1>

          <p className="text-xs text-slate-400">
            Churn Prediction & Sales Forecasting
          </p>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-4">
        {/* Status */}
        <div className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 sm:flex">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/50" />
          <span className="text-xs font-medium text-emerald-300">
            System Online
          </span>
        </div>

        {/* User */}
        <div className="flex items-center gap-3 border-l border-white/10 pl-4">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold text-white">Admin</p>
            <p className="text-xs text-slate-500">Analytics Team</p>
          </div>

          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-sm font-bold text-white ring-2 ring-violet-400/20">
            AD
          </div>
        </div>
      </div>
    </header>
  )
}

export default Navbar