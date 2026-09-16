import KPICard from '../components/dashboard/KPICard'
import SalesForecastChart from '../components/forecasting/SalesForecastChart'
import ProductForecastTable from '../components/forecasting/ProductForecastTable'
import DemandChart from '../components/forecasting/DemandChart'

function SalesForecast() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-violet-400">
          Predictive Analytics
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
          Sales Forecast
        </h1>

        <p className="mt-2 text-sm text-slate-400">
          Forecast future sales and identify products with the highest expected
          demand.
        </p>
      </div>

      {/* KPI Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Next Quarter Sales"
          value="—"
          change="Pending"
          description="forecast output"
          icon="↗"
          trend="up"
        />

        <KPICard
          title="Next Year Sales"
          value="—"
          change="Pending"
          description="annual forecast"
          icon="◷"
          trend="up"
        />

        <KPICard
          title="Predicted Demand"
          value="—"
          change="Pending"
          description="next quarter"
          icon="▥"
          trend="up"
        />

        <KPICard
          title="Forecast Confidence"
          value="—"
          change="Pending"
          description="model confidence"
          icon="✓"
          trend="up"
        />
      </section>

      {/* Sales Forecast */}
      <section>
        <SalesForecastChart />
      </section>

      {/* Product Forecast + Demand */}
      <section className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <ProductForecastTable />
        </div>

        <DemandChart />
      </section>

      {/* Forecast Insight */}
      <section className="relative overflow-hidden rounded-2xl border border-violet-400/10 bg-gradient-to-r from-violet-500/10 via-cyan-500/10 to-emerald-500/10 p-6">
        <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-violet-500/10 blur-3xl" />

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">
            AI Forecast Insight
          </p>

          <h2 className="mt-2 text-xl font-bold text-white">
            Forecast insights will appear once the sales model is connected.
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            The forecasting pipeline will analyze historical sales patterns,
            identify demand trends and seasonality, and generate predictions
            for the upcoming quarter and year. These predictions will also
            support product-level demand and replenishment planning.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <span className="rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-1.5 text-xs font-medium text-violet-300">
              Sales Forecast
            </span>

            <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-medium text-cyan-300">
              Demand Analysis
            </span>

            <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300">
              Product Forecast
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}

export default SalesForecast