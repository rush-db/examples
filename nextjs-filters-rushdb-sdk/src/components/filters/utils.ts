import { useQuery } from '@tanstack/react-query'
import { db } from '@/db'

export function usePropertyValues(propertyId: string) {
  return useQuery({
    queryKey: ['property-values', propertyId],
    queryFn: () => db.properties.values(propertyId),
    select: (data) => data.data,
  })
}

export function calculateMinimalStep(
  min: number,
  max: number,
  precision = 2,
  desiredSteps = 100
) {
  if (precision !== null) {
    return Math.pow(10, -precision)
  } else {
    return (max - min) / desiredSteps
  }
}
