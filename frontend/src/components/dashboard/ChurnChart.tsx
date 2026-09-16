import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const churnData = [
  { month: 'Jan', rate: 4.2 },
  { month: 'Feb', rate: 4.8 },
  { month: 'Mar', rate: 5.1 },
  { month: 'Apr', rate: 6.4 },
  { month: 'May', rate: 5.7 },
  { month: 'Jun', rate: 4.9 },
]

function ChurnChart() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">
          Churn Rate Trend
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Monthly customer churn percentage
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={churnData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="churnGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="rgba(255,255,255,0.06)"
              vertical={false}
            />

            <XAxis
              dataKey="month"
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
              dataKey="rate"
              stroke="#f43f5e"
              strokeWidth={3}
              fill="url(#churnGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ChurnChart