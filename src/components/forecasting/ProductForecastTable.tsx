interface ProductForecast {
  rank: number
  product: string
  category: string
  predictedUnits: number
  growth: number
}

interface ProductForecastTableProps {
  products?: ProductForecast[]
}

function ProductForecastTable({
  products = [],
}: ProductForecastTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="text-lg font-semibold text-white">
          Top Predicted Products
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Products expected to have the highest demand
        </p>
      </div>

      <div className="overflow-x-auto">
        {products.length === 0 ? (
          <div className="flex min-h-40 items-center justify-center px-5 text-sm text-slate-500">
            Product forecast data will appear here once the model is connected.
          </div>
        ) : (
          <table className="w-full min-w-[650px] text-left">
            <thead>
              <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
                <th className="px-5 py-4 font-semibold">Rank</th>
                <th className="px-5 py-4 font-semibold">Product</th>
                <th className="px-5 py-4 font-semibold">Category</th>
                <th className="px-5 py-4 font-semibold">
                  Predicted Units
                </th>
                <th className="px-5 py-4 font-semibold">Growth</th>
              </tr>
            </thead>

            <tbody>
              {products.map((product) => (
                <tr
                  key={`${product.rank}-${product.product}`}
                  className="border-b border-white/5 transition hover:bg-white/[0.03]"
                >
                  <td className="px-5 py-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-400/10 text-sm font-bold text-violet-300">
                      {product.rank}
                    </div>
                  </td>

                  <td className="px-5 py-4">
                    <span className="text-sm font-semibold text-white">
                      {product.product}
                    </span>
                  </td>

                  <td className="px-5 py-4">
                    <span className="rounded-lg bg-cyan-400/10 px-2.5 py-1 text-xs font-medium text-cyan-300">
                      {product.category}
                    </span>
                  </td>

                  <td className="px-5 py-4 text-sm font-semibold text-white">
                    {product.predictedUnits.toLocaleString('en-IN')}
                  </td>

                  <td className="px-5 py-4">
                    <span
                      className={
                        product.growth >= 0
                          ? 'font-semibold text-emerald-400'
                          : 'font-semibold text-red-400'
                      }
                    >
                      {product.growth >= 0 ? '+' : ''}
                      {product.growth.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default ProductForecastTable