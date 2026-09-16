import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const churnTrendData = [
  { period: 'Q1', churnRate: 4.2 },
  { period: 'Q2', churnRate: 5.1 },
  { period: 'Q3', churnRate: 6.4 },
  { period: 'Q4', churnRate: 4.9 },
]

function ChurnTrendChart() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">
          Churn Rate Trend
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Quarterly customer churn performance
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={churnTrendData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient
                id="churnTrendGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor="#8b5cf6"
                  stopOpacity={0.35}
                />

                <stop
                  offset="100%"
                  stopColor="#8b5cf6"
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="rgba(255,255,255,0.06)"
              vertical={false}
            />

            <XAxis
              dataKey="period"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                color: '#fff',
              }}
              formatter={(value) => [
                `${Number(value).toFixed(1)}%`,
                'Churn Rate',
              ]}
            />

            <Area
              type="monotone"
              dataKey="churnRate"
              stroke="#8b5cf6"
              strokeWidth={3}
              fill="url(#churnTrendGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ChurnTrendChart