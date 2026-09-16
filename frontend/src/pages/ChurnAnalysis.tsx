
import ChurnTrendChart from '../components/churn/ChurnTrendChart'
import HighRiskTable from '../components/churn/HighRiskTable'
import BehaviourGroups from '../components/churn/BehaviourGroups'
import RiskDistribution from '../components/dashboard/RiskDistribution'
import KPICard from '../components/dashboard/KPICard'

function ChurnAnalysis() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-red-400">
          Churn Intelligence
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
          Churn Analysis
        </h1>

        <p className="mt-2 text-sm text-slate-400">
          Identify customers at risk and monitor churn patterns across the
          business.
        </p>
      </div>

      {/* KPI Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Current Churn Rate"
          value="4.9%"
          change="-1.2%"
          description="vs previous quarter"
          icon="↘"
          trend="up"
        />

        <KPICard
          title="High-Risk Customers"
          value="1,872"
          change="-6.3%"
          description="from previous period"
          icon="⚠"
          trend="up"
        />

        <KPICard
          title="Medium-Risk Customers"
          value="3,369"
          change="+2.8%"
          description="risk population"
          icon="!"
          trend="down"
        />

        <KPICard
          title="Retention Rate"
          value="95.1%"
          change="+1.2%"
          description="vs previous quarter"
          icon="✓"
          trend="up"
        />
      </section>

      {/* Trend + Risk Distribution */}
      <section className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <ChurnTrendChart />
        </div>

        <RiskDistribution />
      </section>

      {/* High Risk Customers */}
      <section>
        <HighRiskTable />
      </section>

      {/* Behaviour Groups */}
      <section>
        <BehaviourGroups />
      </section>

      {/* Action Insight */}
      <section className="relative overflow-hidden rounded-2xl border border-red-400/10 bg-gradient-to-r from-red-500/10 via-violet-500/10 to-cyan-500/10 p-6">
        <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-red-500/10 blur-3xl" />

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-300">
            Recommended Action
          </p>

          <h2 className="mt-2 text-xl font-bold text-white">
            Prioritize high-risk customers for retention campaigns.
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Customers with a high predicted churn probability should be
            prioritized for targeted offers, personalized communication, and
            proactive retention strategies.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <span className="rounded-full border border-red-400/20 bg-red-400/10 px-3 py-1.5 text-xs font-medium text-red-300">
              High Risk
            </span>

            <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1.5 text-xs font-medium text-amber-300">
              Retention Required
            </span>

            <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-medium text-cyan-300">
              AI Prioritized
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}

export default ChurnAnalysis
