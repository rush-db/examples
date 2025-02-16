import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { useSearchQuery } from '@/context/search-query-context'
import { getFromIndex } from '@/components/labels/utils'
import { labelVariants } from '@/components/labels/constants'
import { useCallback } from 'react'

export function useLabels() {
  const { where, skip, limit } = useSearchQuery()

  const getLabelColor = useCallback((index: number) => {
    const array = Object.keys(labelVariants) as Array<string>
    return getFromIndex(array, index, 0)
  }, [])

  return useQuery({
    queryKey: ['labels', where, skip, limit],
    queryFn: () => db.labels.find({ where, skip, limit }),
    select: (data: Record<string, number>) =>
      Object.entries(data.data).map(([label, value], index) => ({
        label,
        value,
        color: getLabelColor(index),
      })),
    staleTime: 120000,
    placeholderData: keepPreviousData,
  })
}
