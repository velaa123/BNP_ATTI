import { useCallback, useEffect, useState } from 'react'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useApi<T>(
  fetchFunction: () => Promise<T>,
  immediate = true,
): UseApiState<T> & { refetch: () => Promise<void> } {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await fetchFunction()

      setData(result)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to fetch data.',
      )
    } finally {
      setLoading(false)
    }
  }, [fetchFunction])

  useEffect(() => {
    if (immediate) {
      void fetchData()
    }
  }, [fetchData, immediate])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  }
}