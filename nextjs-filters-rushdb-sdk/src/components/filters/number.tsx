import { Slider } from '@/components/ui/slider'
import { FC } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import {
  calculateMinimalStep,
  usePropertyValues,
} from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { useFilters } from '@/context/FiltersContext'

export const NumberFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const { filters, updateFilter } = useFilters()
  const { data, isLoading } = usePropertyValues(property.id)

  if (isLoading) {
    return <Loader />
  }

  if (data && typeof data.min === 'number' && typeof data.max === 'number') {
    return (
      <>
        <Slider
          defaultValue={[data!.min as number, data!.max as number]}
          min={data!.min}
          max={data!.max}
          step={calculateMinimalStep(data!.min!, data!.max!)}
          value={filters[property.name]?.value}
          onValueChange={(newRange) => {
            updateFilter(property, newRange)
          }}
          className="mt-2"
        />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{filters[property.name]?.value?.[0] ?? data!.min!}</span>
          <span>{filters[property.name]?.value?.[1] ?? data!.max!}</span>
        </div>
      </>
    )
  } else {
    return null
  }
}
