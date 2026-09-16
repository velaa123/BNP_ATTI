import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

const riskData = [
  { name: 'Low Risk', value: 58 },
  { name: 'Medium Risk', value: 27 },
  { name: 'High Risk', value: 15 },
]

const riskColors = ['#10b981', '#f59e0b', '#ef4444']

function RiskDistribution() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">
          Customer Risk Distribution
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Customers grouped by churn probability
        </p>
      </div>

      <div className="relative h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={riskData}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={90}
              paddingAngle={4}
              dataKey="value"
              stroke="none"
            >
              {riskData.map((entry, index) => (
                <Cell key={entry.name} fill={riskColors[index]} />
              ))}
            </Pie>

            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                color: '#fff',
              }}
              formatter={(value) => [`${value}%`, 'Customers']}
            />
          </PieChart>
        </ResponsiveContainer>

        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">100%</p>
            <p className="text-xs text-slate-500">Customers</p>
          </div>
        </div>
      </div>

      <div className="mt-2 grid grid-cols-3 gap-2">
        {riskData.map((item, index) => (
          <div
            key={item.name}
            className="rounded-xl bg-white/[0.03] p-3 text-center"
          >
            <div className="mb-1 flex items-center justify-center gap-2">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: riskColors[index] }}
              />

              <span className="text-xs text-slate-400">
                {item.name}
              </span>
            </div>

            <p className="text-lg font-bold text-white">
              {item.value}%
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RiskDistribution