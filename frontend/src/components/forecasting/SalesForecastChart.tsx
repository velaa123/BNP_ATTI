import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface SalesForecastPoint {
  period: string
  actual?: number
  forecast?: number
}

interface SalesForecastChartProps {
  data?: SalesForecastPoint[]
}

function SalesForecastChart({ data = [] }: SalesForecastChartProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">
          Sales Forecast
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Historical sales vs predicted future sales
        </p>
      </div>

      <div className="h-72 w-full">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Forecast data will appear here once the model is connected.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
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
                tickFormatter={(value) => `₹${value / 1000}k`}
              />

              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  color: '#fff',
                }}
                formatter={(value, name) => [
                  value !== undefined && value !== null
                    ? `₹${Number(value).toLocaleString('en-IN')}`
                    : '-',
                  name === 'actual' ? 'Actual Sales' : 'Forecast',
                ]}
              />

              <Legend
                wrapperStyle={{
                  paddingTop: '15px',
                  fontSize: '12px',
                }}
              />

              <Line
                type="monotone"
                dataKey="actual"
                name="Actual Sales"
                stroke="#22d3ee"
                strokeWidth={3}
                dot={{ r: 4 }}
                connectNulls={false}
              />

              <Line
                type="monotone"
                dataKey="forecast"
                name="Forecast"
                stroke="#a78bfa"
                strokeWidth={3}
                strokeDasharray="6 4"
                dot={{ r: 4 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default SalesForecastChart