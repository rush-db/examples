import { useMutation, useQueryClient } from '@tanstack/react-query'
import { db } from '@/db'

export function useDeleteAllRecords() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => db.records.delete({ where: {} }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [
          'records',
          'labels',
          'properties',
          'property-values',
          'record-relations',
        ],
      })
    },
  })
}
