import KPICard from '../components/dashboard/KPICard'
import RiskBadge from '../components/churn/RiskBadge'
import Loading from '../components/common/Loading'
import ErrorMessage from '../components/common/ErrorMessage'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'

// Maps whatever risk/retention wording the backend returns onto the
// three visual tones the RiskBadge component supports. Real model
// segment names aren't fixed strings we can hardcode against, so this
// falls back to 'Medium' rather than guessing wrong.
function inferRiskTone(segmentName: string, retentionPriority: string): 'Low' | 'Medium' | 'High' {
  const text = `${segmentName} ${retentionPriority}`.toUpperCase()
  if (text.includes('CRITICAL') || text.includes('HIGH') || text.includes('AT_RISK') || text.includes('URGENT')) {
    return 'High'
  }
  if (text.includes('STABLE') || text.includes('LOW') || text.includes('LOYAL')) {
    return 'Low'
  }
  return 'Medium'
}

function CustomerSegments() {
  const { data, loading, error } = useApi(api.getCustomerSegments)

  if (loading) {
    return <Loading />
  }

  if (error) {
    return <ErrorMessage message={error} />
  }

  const rows = data ?? []
  const totalCustomers = rows.length

  // Group real rows by whatever customer_segment values actually exist —
  // not a fixed set of 3 names, since the model's real segment names
  // differ from the mock's.
  const grouped = rows.reduce<Record<string, typeof rows>>((acc, row) => {
    const key = row.customer_segment || 'UNKNOWN'
    if (!acc[key]) acc[key] = []
    acc[key].push(row)
    return acc
  }, {})

  const segments = Object.entries(grouped)
    .map(([name, segmentRows]) => {
      const count = segmentRows.length
      const percentage = totalCustomers > 0 ? Math.round((count / totalCustomers) * 100) : 0
      const retentionPriority = segmentRows[0]?.retention_priority || ''
      const recommendedAction = segmentRows[0]?.recommended_action || 'No action specified'
      const risk = inferRiskTone(name, retentionPriority)

      return { name, count, percentage, recommendedAction, risk }
    })
    .sort((a, b) => b.count - a.count)

  const highRiskCount = segments.filter((s) => s.risk === 'High').reduce((sum, s) => sum + s.count, 0)
  const mediumRiskCount = segments.filter((s) => s.risk === 'Medium').reduce((sum, s) => sum + s.count, 0)
  const lowRiskCount = segments.filter((s) => s.risk === 'Low').reduce((sum, s) => sum + s.count, 0)

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

      {totalCustomers === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-sm text-slate-500">
          Segment data will appear here once the model is connected.
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KPICard
              title="Total Customers"
              value={totalCustomers.toLocaleString('en-IN')}
              description="analyzed customers"
              icon="👥"
            />

            <KPICard
              title="Low Risk"
              value={lowRiskCount.toLocaleString('en-IN')}
              change={`${Math.round((lowRiskCount / totalCustomers) * 100)}%`}
              description="customer base"
              icon="✓"
              trend="up"
            />

            <KPICard
              title="Medium Risk"
              value={mediumRiskCount.toLocaleString('en-IN')}
              change={`${Math.round((mediumRiskCount / totalCustomers) * 100)}%`}
              description="customer base"
              icon="!"
              trend="neutral"
            />

            <KPICard
              title="High Risk"
              value={highRiskCount.toLocaleString('en-IN')}
              change={`${Math.round((highRiskCount / totalCustomers) * 100)}%`}
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

                  <div className="mt-6">
                    <p className="text-3xl font-bold text-white">
                      {segment.count.toLocaleString('en-IN')}
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

                  <div className="mt-5 rounded-xl bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">
                      Recommended action
                    </p>

                    <p className="mt-1 text-sm font-semibold text-white">
                      {segment.recommendedAction}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  )
}

export default CustomerSegments