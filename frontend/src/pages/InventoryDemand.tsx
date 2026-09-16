import KPICard from '../components/dashboard/KPICard'
import DemandChart from '../components/forecasting/DemandChart'
import InventoryTable from '../components/inventory/InventoryTable'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'

function InventoryDemand() {
  const { data: inventory } = useApi(api.getInventory)

  const items = inventory ?? []
  const totalPredictedDemand = items.reduce((sum, item) => sum + item.predictedDemand, 0)
  const highPriorityCount = items.filter((item) => item.reorderPriority === 'High').length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-400">
          Supply Intelligence
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
          Inventory & Demand
        </h1>

        <p className="mt-2 text-sm text-slate-400">
          Use predicted product demand to identify replenishment priorities
          and support inventory planning.
        </p>
      </div>

      {/* KPI Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Predicted Demand"
          value={items.length > 0 ? `${totalPredictedDemand.toLocaleString('en-IN')} units` : '—'}
          change={items.length > 0 ? undefined : 'Pending'}
          description="across all products"
          icon="↗"
          trend="up"
        />

        <KPICard
          title="High Priority Products"
          value={items.length > 0 ? highPriorityCount.toLocaleString('en-IN') : '—'}
          change={items.length > 0 ? undefined : 'Pending'}
          description="require replenishment focus"
          icon="!"
          trend="up"
        />

        <KPICard
          title="Demand Growth"
          value="—"
          change="Pending"
          description="vs previous period"
          icon="↗"
          trend="up"
        />

        <KPICard
          title="Forecast Horizon"
          value="3M"
          change="Stable"
          description="demand forecast"
          icon="◷"
          trend="up"
        />
      </section>

      {/* Demand Forecast */}
      <section>
        <DemandChart />
      </section>

      {/* Demand-Based Reorder Recommendations */}
      <section>
        <InventoryTable />
      </section>

      {/* Demand Recommendation */}
      <section className="relative overflow-hidden rounded-2xl border border-emerald-400/10 bg-gradient-to-r from-emerald-500/10 via-cyan-500/10 to-violet-500/10 p-6">
        <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">
            AI Demand Recommendation
          </p>

          <h2 className="mt-2 text-xl font-bold text-white">
            Focus replenishment planning on products with rising predicted
            demand.
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Demand forecasts can help identify products that may require
            additional replenishment planning in the upcoming period.
            Prioritize products with strong predicted demand while avoiding
            unnecessary overstocking.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <span className="rounded-full border border-red-400/20 bg-red-400/10 px-3 py-1.5 text-xs font-medium text-red-300">
              High Reorder Priority
            </span>

            <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1.5 text-xs font-medium text-amber-300">
              Monitor Demand
            </span>

            <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-medium text-cyan-300">
              Demand Forecast
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}

export default InventoryDemand