interface RiskBadgeProps {
  risk: 'Low' | 'Medium' | 'High'
}

function RiskBadge({ risk }: RiskBadgeProps) {
  const styles = {
    Low: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
    Medium: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
    High: 'border-red-400/20 bg-red-400/10 text-red-300',
  }

  const dots = {
    Low: 'bg-emerald-400',
    Medium: 'bg-amber-400',
    High: 'bg-red-400',
  }

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${styles[risk]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dots[risk]}`} />

      {risk} Risk
    </span>
  )
}

export default RiskBadge