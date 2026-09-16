import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface DemandForecastPoint {
  period: string
  demand: number
}

interface DemandChartProps {
  data?: DemandForecastPoint[]
}

function DemandChart({ data = [] }: DemandChartProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">
          Demand Forecast
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Expected product demand by forecast period
        </p>
      </div>

      <div className="h-72 w-full">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Demand forecast data will appear here once the model is connected.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
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
                tickFormatter={(value) => `${value / 1000}k`}
              />

              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  color: '#fff',
                }}
                formatter={(value) => [
                  `${Number(value).toLocaleString('en-IN')} units`,
                  'Demand',
                ]}
              />

              <Bar
                dataKey="demand"
                name="Predicted Demand"
                fill="#06b6d4"
                radius={[8, 8, 0, 0]}
                maxBarSize={48}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default DemandChart