interface ReorderPriorityProps {
  priority: 'Low' | 'Medium' | 'High'
}

function ReorderPriority({ priority }: ReorderPriorityProps) {
  const styles = {
    High: {
      badge: 'border-red-400/20 bg-red-400/10 text-red-300',
      dot: 'bg-red-400',
    },
    Medium: {
      badge: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
      dot: 'bg-amber-400',
    },
    Low: {
      badge: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
      dot: 'bg-emerald-400',
    },
  }

  const currentStyle = styles[priority]

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${currentStyle.badge}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${currentStyle.dot}`}
      />

      {priority}
    </span>
  )
}

export default ReorderPriority