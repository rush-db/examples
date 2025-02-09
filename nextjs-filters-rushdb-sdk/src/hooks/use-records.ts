import { useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { SearchQuery } from '@rushdb/javascript-sdk'
import { useFilters } from '@/context/filter-context'
import {
  processStringValuePart,
  processNumberValuePart,
  processDatetimeValuePart,
  canProcessValuePart,
} from '@/lib/filter-utils'

export function useRecords() {
  const { filters } = useFilters()

  const query: SearchQuery = {
    where: {},
  }

  Object.entries(filters).forEach(([key, propertyData]) => {
    if (canProcessValuePart(propertyData.value)) {
      switch (propertyData.type) {
        case 'string': {
          query.where = {
            ...query.where,
            [key]: processStringValuePart(
              propertyData.value as string | string[]
            ),
          }
          break
        }
        case 'boolean': {
          query.where = {
            ...query.where,
            [key]: propertyData.value as boolean,
          }
          break
        }
        case 'number': {
          query.where = {
            ...query.where,
            [key]: processNumberValuePart(
              propertyData.value as number | number[]
            ),
          }
          break
        }
        case 'datetime': {
          const date = processDatetimeValuePart(
            propertyData.value as {
              from?: string
              to?: string
            }
          )
          const hasDateFilters = Object.keys(date).length > 0

          query.where = {
            ...query.where,
            ...(hasDateFilters && {
              [key]: processDatetimeValuePart(
                propertyData.value as {
                  from?: string
                  to?: string
                }
              ),
            }),
          }
          break
        }
      }
    }
  })

  return useQuery({
    queryKey: ['records', filters],
    queryFn: () => db.records.find(query),
    staleTime: 120000,
  })
}
