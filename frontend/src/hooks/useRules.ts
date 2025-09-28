import { useEffect, useState } from 'react'

import type { ApiClient, RuleSummary } from '../api/client'

export function useRules(client: ApiClient) {
  const [rules, setRules] = useState<RuleSummary[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    void client
      .listRules()
      .then((items) => {
        if (!cancelled) {
          setRules(items)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [client])

  return { rules, loading }
}

export default useRules
