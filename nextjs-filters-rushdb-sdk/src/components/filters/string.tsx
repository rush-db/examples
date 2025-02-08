import { FC, useEffect, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { usePropertyValues } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { useFilters } from '@/context/FiltersContext'

export const StringFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const { filters, updateFilter } = useFilters()

  const [options, setOptions] = useState<string[]>(
    filters[property.name]?.value || []
  )
  const [isDirty, setIsDirty] = useState(false)

  const { data, isLoading } = usePropertyValues(property.id)

  useEffect(() => {
    if (isDirty) {
      updateFilter(property, options)
    }
  }, [options, property, updateFilter, isDirty])

  if (isLoading) {
    return <Loader />
  }

  if (data && Array.isArray(data.values)) {
    return (
      <>
        <div className="space-y-2">
          {(data.values as string[]).map((category) => (
            <div key={category} className="flex items-center space-x-2">
              <Checkbox
                id={category}
                checked={options.includes(category)}
                onCheckedChange={(checked) => {
                  setOptions(
                    checked
                      ? [...options, category]
                      : options.filter((c) => c !== category)
                  )
                  setIsDirty(true)
                }}
              />
              <Label htmlFor={category}>{category}</Label>
            </div>
          ))}
        </div>
      </>
    )
  } else {
    return null
  }
}
