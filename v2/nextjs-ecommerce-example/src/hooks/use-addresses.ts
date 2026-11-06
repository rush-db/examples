import { useFetchQuery } from '@/hooks/use-fetch-query'

export type Address = {
  id: string
  city: string
  street: string
  postalCode: string
  country: string
  name?: string
}

export function useAddresses() {
  const { data, isLoading, error } = useFetchQuery<Address[]>({
    fetcher: async (signal) => {
      const res = await fetch('/api/addresses', { signal })
      if (!res.ok) throw new Error('Failed to load addresses')
      const json = await res.json()
      return json.data as Address[]
    },
    deps: [],
    keepPreviousData: true,
  })

  return { data, isLoading, error }
}
