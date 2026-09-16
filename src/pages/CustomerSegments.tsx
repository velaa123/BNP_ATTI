import KPICard from '../components/dashboard/KPICard'
import RiskBadge from '../components/churn/RiskBadge'

const segments = [
  {
    name: 'Low Risk',
    description: 'Customers with a low probability of churning.',
    customers: 7238,
    percentage: 58,
    avgProbability: '18%',
    risk: 'Low' as const,
    action: 'Maintain engagement',
  },
  {
    name: 'Medium Risk',
    description: 'Customers showing early signs of churn risk.',
    customers: 3370,
    percentage: 27,
    avgProbability: '46%',
    risk: 'Medium' as const,
    action: 'Targeted engagement',
  },
  {
    name: 'High Risk',
    description: 'Customers with a high probability of churning.',
    customers: 1872,
    percentage: 15,
    avgProbability: '82%',
    risk: 'High' as const,
    action: 'Immediate retention',
  },
]

function CustomerSegments() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
          Customer Intelligence
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
          Customer Segments
        </h1>

        <p className="mt-2 text-sm text-slate-400">
          Segment customers according to their predicted churn probability
          and prioritize retention strategies.
        </p>
      </div>

      {/* KPI Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Total Customers"
          value="12,480"
          description="analyzed customers"
          icon="👥"
        />

        <KPICard
          title="Low Risk"
          value="7,238"
          change="58%"
          description="customer base"
          icon="✓"
          trend="up"
        />

        <KPICard
          title="Medium Risk"
          value="3,370"
          change="27%"
          description="customer base"
          icon="!"
          trend="neutral"
        />

        <KPICard
          title="High Risk"
          value="1,872"
          change="15%"
          description="customer base"
          icon="⚠"
          trend="down"
        />
      </section>

      {/* Segment Cards */}
      <section className="grid gap-6 lg:grid-cols-3">
        {segments.map((segment) => (
          <div
            key={segment.name}
            className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:border-white/20"
          >
            <div
              className={`absolute -right-12 -top-12 h-32 w-32 rounded-full blur-3xl ${
                segment.risk === 'Low'
                  ? 'bg-emerald-400/10'
                  : segment.risk === 'Medium'
                    ? 'bg-amber-400/10'
                    : 'bg-red-400/10'
              }`}
            />

            <div className="relative">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">
                  {segment.name}
                </h2>

                <RiskBadge risk={segment.risk} />
              </div>

              <p className="mt-3 min-h-10 text-sm leading-5 text-slate-500">
                {segment.description}
              </p>

              <div className="mt-6">
                <p className="text-3xl font-bold text-white">
                  {segment.customers.toLocaleString('en-IN')}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  customers
                </p>
              </div>

              <div className="mt-5">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    Customer share
                  </span>

                  <span className="text-sm font-semibold text-white">
                    {segment.percentage}%
                  </span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full ${
                      segment.risk === 'Low'
                        ? 'bg-emerald-400'
                        : segment.risk === 'Medium'
                          ? 'bg-amber-400'
                          : 'bg-red-400'
                    }`}
                    style={{ width: `${segment.percentage}%` }}
                  />
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-white/[0.03] p-3">
                  <p className="text-xs text-slate-500">
                    Avg. churn probability
                  </p>

                  <p className="mt-1 text-sm font-semibold text-white">
                    {segment.avgProbability}
                  </p>
                </div>

                <div className="rounded-xl bg-white/[0.03] p-3">
                  <p className="text-xs text-slate-500">
                    Recommended action
                  </p>

                  <p className="mt-1 text-sm font-semibold text-white">
                    {segment.action}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* Segment Strategy */}
      <section className="relative overflow-hidden rounded-2xl border border-cyan-400/10 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-fuchsia-500/10 p-6">
        <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-cyan-500/10 blur-3xl" />

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
            Retention Strategy
          </p>

          <h2 className="mt-2 text-xl font-bold text-white">
            Different risk groups need different customer strategies.
          </h2>

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-emerald-400/10 bg-emerald-400/5 p-4">
              <p className="text-sm font-semibold text-emerald-300">
                Low Risk
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-400">
                Maintain loyalty with regular engagement, rewards, and
                personalized recommendations.
              </p>
            </div>

            <div className="rounded-xl border border-amber-400/10 bg-amber-400/5 p-4">
              <p className="text-sm font-semibold text-amber-300">
                Medium Risk
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-400">
                Use targeted offers and proactive communication to prevent
                customers from becoming high risk.
              </p>
            </div>

            <div className="rounded-xl border border-red-400/10 bg-red-400/5 p-4">
              <p className="text-sm font-semibold text-red-300">
                High Risk
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-400">
                Prioritize immediate retention campaigns for customers with
                the highest predicted churn probability.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default CustomerSegments