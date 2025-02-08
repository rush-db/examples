import { FC, useEffect, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { usePropertyValues } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useFilters } from '@/context/FiltersContext'

export const BooleanFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const { filters, updateFilter } = useFilters()
  const [checked, setChecked] = useState(filters[property.name]?.value || false)
  const [isDirty, setIsDirty] = useState(false)

  const { data, isLoading } = usePropertyValues(property.id)
  useEffect(() => {
    if (isDirty) {
      updateFilter(property, checked)
    }
  }, [checked, property, updateFilter, isDirty])

  if (isLoading) {
    return <Loader />
  }

  if (data && Array.isArray(data.values)) {
    return (
      <div className="flex items-center space-x-2 justify-between w-full">
        <Label htmlFor={property.name + property.type}>{property.name}</Label>
        <Switch
          id={property.name + property.type}
          checked={checked}
          onCheckedChange={(newValue) => {
            setChecked(newValue)
            setIsDirty(true)
          }}
        />
      </div>
    )
  } else {
    return null
  }
}
