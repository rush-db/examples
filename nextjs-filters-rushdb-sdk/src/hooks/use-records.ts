import { useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { SearchQuery } from '@rushdb/javascript-sdk'
import { useFilters } from '@/context/FiltersContext'

// @TODO: refactor: normalize single pair filters with $gte && $lte
function processStringValuePart(value: string | string[]) {
  if (Array.isArray(value)) {
    return {
      $in: value,
    }
  }

  return {
    $contains: value,
  }
}

function processNumberValuePart(value: number | number[]) {
  if (Array.isArray(value)) {
    const [min, max] = value

    return {
      $gte: min,
      $lte: max,
    }
  }

  return {
    $gte: value,
  }
}

function processDatetimeValuePart(value: string | string[]) {
  if (Array.isArray(value)) {
    const [min, max] = value

    return {
      $gte: min,
      $lte: max,
    }
  }

  return {
    $gte: value,
  }
}

function canProcessValuePart(value: any) {
  if (!value) {
    return
  }

  if (Array.isArray(value) && !value.length) {
    return
  }

  return true
}

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
          query.where = {
            ...query.where,
            [key]: processDatetimeValuePart(
              propertyData.value as string | string[]
            ),
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
