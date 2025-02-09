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
  const { data, isLoading } = usePropertyValues(property.id)
  const { filters, updateFilter } = useFilters()

  if (isLoading) {
    return <Loader />
  }

  if (data && typeof data.min === 'number' && typeof data.max === 'number') {
    const currentRange = filters[property.name]?.value || [data.min, data.max]

    return (
      <>
        <Slider
          defaultValue={[data!.min as number, data!.max as number]}
          min={data!.min}
          max={data!.max}
          step={calculateMinimalStep(data!.min!, data!.max!)}
          value={currentRange}
          onValueChange={(newRange) => {
            updateFilter(property, newRange)
          }}
          className="mt-2"
        />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{currentRange[0]}</span>
          <span>{currentRange[1]}</span>
        </div>
      </>
    )
  } else {
    return null
  }
}
