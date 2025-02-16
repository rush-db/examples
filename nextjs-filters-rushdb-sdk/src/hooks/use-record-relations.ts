import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { db } from '@/db'

export function useRecordRelations(id: string) {
  return useQuery({
    queryKey: ['record-relations', id],
    queryFn: () => db.records.relations(id),
    select: (data) => {
      return data.data
    },
    placeholderData: keepPreviousData,
  })
}
