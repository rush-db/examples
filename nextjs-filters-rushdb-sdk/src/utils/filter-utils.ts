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
  if (!value) {
    return false
  }
  if (Array.isArray(value) && value.length === 0) {
    return false
  }
  return true
}
