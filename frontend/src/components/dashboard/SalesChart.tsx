import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const salesData = [
  { month: 'Jan', sales: 42000 },
  { month: 'Feb', sales: 48000 },
  { month: 'Mar', sales: 45000 },
  { month: 'Apr', sales: 56000 },
  { month: 'May', sales: 62000 },
  { month: 'Jun', sales: 68000 },
]

function SalesChart() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">
          Sales Performance
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Monthly sales trend
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={salesData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
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
              tickFormatter={(value) => `₹${value / 1000}k`}
            />

            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                color: '#fff',
              }}
              formatter={(value) => [
                `₹${Number(value).toLocaleString('en-IN')}`,
                'Sales',
              ]}
            />

            <Line
              type="monotone"
              dataKey="sales"
              stroke="#22d3ee"
              strokeWidth={3}
              dot={{
                r: 4,
                fill: '#22d3ee',
                strokeWidth: 2,
                stroke: '#0f172a',
              }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default SalesChart