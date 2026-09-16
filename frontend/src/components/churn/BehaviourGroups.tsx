
const groups = [
  {
    name: 'Group 0',
    description: 'Low-risk, highly engaged customers',
    customers: 7238,
    percentage: 58,
    action: 'Maintain engagement',
    icon: '◉',
  },
  {
    name: 'Group 1',
    description: 'Customers showing declining activity',
    customers: 3370,
    percentage: 27,
    action: 'Target with retention offers',
    icon: '◌',
  },
  {
    name: 'Group 2',
    description: 'Customers with strong churn signals',
    customers: 1872,
    percentage: 15,
    action: 'Immediate retention action',
    icon: '⚠',
  },
]

function BehaviourGroups() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-white">
          Behaviour Groups
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Customer groups identified from behavioural patterns
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {groups.map((group) => (
          <div
            key={group.name}
            className="rounded-xl border border-white/10 bg-slate-900/60 p-4 transition duration-200 hover:border-cyan-400/20 hover:bg-white/[0.04]"
          >
            <div className="flex items-start justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-lg text-cyan-300">
                {group.icon}
              </div>

              <span className="text-2xl font-bold text-white">
                {group.percentage}%
              </span>
            </div>

            <h3 className="mt-4 text-base font-semibold text-white">
              {group.name}
            </h3>

            <p className="mt-1 min-h-10 text-xs leading-5 text-slate-500">
              {group.description}
            </p>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500"
                style={{ width: `${group.percentage}%` }}
              />
            </div>

            <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
              <div>
                <p className="text-xs text-slate-500">Customers</p>
                <p className="mt-1 text-sm font-semibold text-white">
                  {group.customers.toLocaleString('en-IN')}
                </p>
              </div>

              <div className="max-w-[150px] text-right">
                <p className="text-xs text-slate-500">Recommended</p>
                <p className="mt-1 text-xs font-medium text-cyan-300">
                  {group.action}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default BehaviourGroups
