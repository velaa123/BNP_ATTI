const inventoryData = [
  {
    product: 'Wireless Headphones',
    category: 'Electronics',
    demand: 680,
    priority: 'High',
  },
  {
    product: 'Smart Watch',
    category: 'Electronics',
    demand: 620,
    priority: 'Medium',
  },
  {
    product: 'Running Shoes',
    category: 'Footwear',
    demand: 540,
    priority: 'High',
  },
  {
    product: 'Laptop Backpack',
    category: 'Accessories',
    demand: 480,
    priority: 'Low',
  },
  {
    product: 'Bluetooth Speaker',
    category: 'Electronics',
    demand: 420,
    priority: 'Medium',
  },
]

const priorityStyles = {
  High: 'bg-red-400/10 text-red-300 border-red-400/20',
  Medium: 'bg-amber-400/10 text-amber-300 border-amber-400/20',
  Low: 'bg-emerald-400/10 text-emerald-300 border-emerald-400/20',
}

function InventoryTable() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="text-lg font-semibold text-white">
          Demand & Reorder Recommendations
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Products ranked by predicted demand and reorder priority
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[700px] text-left">
          <thead>
            <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
              <th className="px-5 py-4 font-semibold">Product</th>
              <th className="px-5 py-4 font-semibold">Category</th>
              <th className="px-5 py-4 font-semibold">
                Predicted Demand
              </th>
              <th className="px-5 py-4 font-semibold">
                Reorder Priority
              </th>
            </tr>
          </thead>

          <tbody>
            {inventoryData.map((item) => (
              <tr
                key={item.product}
                className="border-b border-white/5 transition hover:bg-white/[0.03]"
              >
                <td className="px-5 py-4">
                  <span className="text-sm font-semibold text-white">
                    {item.product}
                  </span>
                </td>

                <td className="px-5 py-4 text-sm text-slate-300">
                  {item.category}
                </td>

                <td className="px-5 py-4 text-sm font-semibold text-white">
                  {item.demand.toLocaleString('en-IN')} units
                </td>

                <td className="px-5 py-4">
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                      priorityStyles[
                        item.priority as keyof typeof priorityStyles
                      ]
                    }`}
                  >
                    {item.priority}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default InventoryTable