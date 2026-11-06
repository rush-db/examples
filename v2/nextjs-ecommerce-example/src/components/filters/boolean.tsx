import { FC } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { Loader } from 'lucide-react'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { usePropertyValues } from '@/hooks/use-property-values'

export const BooleanFilter: FC<{
  property: Property
  onChange: (value: boolean) => void
  value: boolean
}> = ({ property, value, onChange }) => {
  const { data, isLoading } = usePropertyValues(property.id)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader className="h-4 w-4 animate-spin" />
      </div>
    )
  }

  if (data && Array.isArray(data.values)) {
    return (
      <div className="flex items-center space-x-2 justify-between w-full">
        <Label htmlFor={property.name + property.type}>{property.name}</Label>
        <Switch
          id={property.name + property.type}
          checked={Boolean(value)}
          onCheckedChange={onChange}
        />
      </div>
    )
  } else {
    return null
  }
}
