import { FC } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { usePropertyValues } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { useFilters } from '@/context/filter-context'

export const StringFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const { filters, updateFilter } = useFilters()
  const { data, isLoading } = usePropertyValues(property.id)

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
                checked={filters[property.name]?.value?.includes(category)}
                onCheckedChange={(checked) => {
                  const value = checked
                    ? [...(filters[property.name]?.value || []), category]
                    : (filters[property.name]?.value || []).filter(
                        (c) => c !== category
                      )

                  updateFilter(property, value)
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
