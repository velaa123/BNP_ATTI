import { useEffect, useState } from 'react'
import KPICard from '../components/dashboard/KPICard'
import SalesChart from '../components/dashboard/SalesChart'
import ChurnChart from '../components/dashboard/ChurnChart'
import RiskDistribution from '../components/dashboard/RiskDistribution'
import HighRiskTable from '../components/churn/HighRiskTable'
import { api } from '../services/api'
import type { DashboardSummary } from '../types'

function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDashboardSummary = async () => {
      try {
        setLoading(true)
        setError(null)

        const data = await api.getDashboardSummary()
        setSummary(data)
      } catch (err) {
        console.error('Failed to load dashboard summary:', err)
        setError('Unable to load dashboard summary.')
      } finally {
        setLoading(false)
      }
    }

    loadDashboardSummary()
  }, [])

  const formatNumber = (value: number) =>
    new Intl.NumberFormat('en-IN').format(value)

  const formatRevenue = (value: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400">
          Overview
        </p>

        <div className="mt-2 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Customer Intelligence
            </h1>

            <p className="mt-2 text-sm text-slate-400">
              Monitor churn risk, sales performance, and business forecasts.
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2">
            <p className="text-xs text-slate-500">Reporting Period</p>
            <p className="mt-1 text-sm font-semibold text-white">
              Current Quarter
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Total Customers"
          value={
            loading
              ? '...'
              : summary
                ? formatNumber(summary.totalCustomers)
                : '—'
          }
          change=""
          description="Current customer base"
          icon="👥"
          trend="up"
        />

        <KPICard
          title="Churn Rate"
          value={
            loading
              ? '...'
              : summary
                ? `${summary.churnRate}%`
                : '—'
          }
          change=""
          description="Current churn rate"
          icon="↘"
          trend="up"
        />

        <KPICard
          title="Quarterly Revenue"
          value={
            loading
              ? '...'
              : summary
                ? formatRevenue(summary.revenue)
                : '—'
          }
          change=""
          description="Current quarter revenue"
          icon="₹"
          trend="up"
        />

        <KPICard
          title="High-Risk Customers"
          value={
            loading
              ? '...'
              : summary
                ? formatNumber(summary.highRiskCustomers)
                : '—'
          }
          change=""
          description="Current high-risk population"
          icon="⚠"
          trend="up"
        />
      </section>

      {error && (
        <div className="rounded-xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Main Charts */}
      <section className="grid gap-6 xl:grid-cols-2">
        <SalesChart />
        <ChurnChart />
      </section>

      {/* Risk + Quick Insights */}
      <section className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <HighRiskTable />
        </div>

        <RiskDistribution />
      </section>

      {/* Bottom Insight Banner */}
      <section className="relative overflow-hidden rounded-2xl border border-cyan-400/10 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-fuchsia-500/10 p-6">
        <div className="absolute -right-20 -top-20 h-48 w-48 rounded-full bg-violet-500/10 blur-3xl" />

        <div className="relative flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
              AI Business Insight
            </p>

            <h2 className="mt-2 text-xl font-bold text-white">
              Customer churn is showing a positive downward trend.
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              The current dashboard indicates improving customer retention,
              while a focused intervention on high-risk customers could
              further reduce future churn.
            </p>
          </div>

          <button className="shrink-0 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-50">
            View Insights
          </button>
        </div>
      </section>
    </div>
  )
}

export default Dashboard