
import RiskBadge from './RiskBadge'
import Loading from '../common/Loading'
import ErrorMessage from '../common/ErrorMessage'
import { api } from '../../services/api'
import { useApi } from '../../hooks/useApi'

function HighRiskTable() {
 const {
  data: customers,
  loading,
  error,
} = useApi(api.getHighRiskCustomers)

  if (loading) {
    return <Loading />
  }

  if (error) {
  return <ErrorMessage message={error} />
}

  const highRiskCustomers = customers ?? []

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold text-white">
            High-Risk Customers
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Customers most likely to churn next quarter
          </p>
        </div>

        <span className="rounded-full bg-red-400/10 px-3 py-1 text-xs font-semibold text-red-300">
          Top 10
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left">
          <thead>
            <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
              <th className="px-5 py-4 font-semibold">Customer ID</th>
              <th className="px-5 py-4 font-semibold">Churn Probability</th>
              <th className="px-5 py-4 font-semibold">Risk</th>
              <th className="px-5 py-4 font-semibold">Source</th>
            </tr>
          </thead>

          <tbody>
            {highRiskCustomers.map((customer) => {
              const probability = customer.churnProbability * 100

              const risk =
                customer.risk.charAt(0).toUpperCase() +
                customer.risk.slice(1).toLowerCase()

              return (
                <tr
                  key={customer.id}
                  className="border-b border-white/5 transition hover:bg-white/[0.03]"
                >
                  <td className="px-5 py-4">
                    <span className="text-sm font-semibold text-white">
                      {customer.id}
                    </span>
                  </td>

                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-orange-400 to-red-500"
                          style={{ width: `${probability}%` }}
                        />
                      </div>

                      <span className="text-sm font-semibold text-white">
                        {probability.toFixed(1)}%
                      </span>
                    </div>
                  </td>

                  <td className="px-5 py-4">
                    <RiskBadge risk={risk as 'Low' | 'Medium' | 'High'} />
                  </td>

                  <td className="px-5 py-4">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        customer.source === 'model'
                          ? 'bg-cyan-400/10 text-cyan-300'
                          : 'bg-amber-400/10 text-amber-300'
                      }`}
                    >
                      {customer.source === 'model' ? 'ML Model' : 'Mock'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default HighRiskTable
