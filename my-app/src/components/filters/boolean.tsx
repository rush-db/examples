import { FC, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { usePropertyValues } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

export const BooleanFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const [checked, setChecked] = useState(false)

  const { data, isLoading } = usePropertyValues(property.id)

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
          onCheckedChange={setChecked}
        />
      </div>
    )
  } else {
    return null
  }
}
