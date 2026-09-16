export function formatNumber(value: number): string {
  return value.toLocaleString('en-IN')
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatCurrencyInCrores(value: number): string {
  return `₹${(value / 10000000).toFixed(2)} Cr`
}

export function formatUnits(value: number): string {
  return `${formatNumber(value)} units`
}