import { Property, PropertyValue, SearchQuery } from '@rushdb/javascript-sdk'

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

export function processStringValuePart(value: string | string[]) {
  if (Array.isArray(value)) {
    return { $in: value }
  }
  return { $contains: value }
}

export function processNumberValuePart(value: number | number[]) {
  if (Array.isArray(value)) {
    const [min, max] = value
    return { $gte: min, $lte: max }
  }
  return { $gte: value }
}

export function processDatetimeValuePart({
  from,
  to,
}: {
  from?: string
  to?: string
}) {
  const result: { $gte?: string; $lte?: string } = {}
  if (from) {
    result.$gte = from
  }
  if (to) {
    result.$lte = to
  }
  return result
}

export function canProcessValuePart(value: any): boolean {
  if (typeof value === 'undefined') {
    return false
  }

  return !(Array.isArray(value) && value.length === 0)
}

export const processPropertyValue = (
  property: Property,
  value: PropertyValue
): any => {
  if (canProcessValuePart(value)) {
    switch (property.type) {
      case 'string': {
        return processStringValuePart(value as string | string[])
      }
      case 'boolean': {
        return value as boolean
      }
      case 'number': {
        return processNumberValuePart(value as number | number[])
      }
      case 'datetime': {
        const date = processDatetimeValuePart(
          value as {
            from?: string
            to?: string
          }
        )
        const hasDateFilters = Object.keys(date).length > 0
        if (hasDateFilters) {
          return processDatetimeValuePart(
            value as {
              from?: string
              to?: string
            }
          )
        }
      }
    }
  }
}
export const pickValue = <T>(where: SearchQuery['where'] = {}, key: string) =>
  where[key as keyof SearchQuery['where']] as T
