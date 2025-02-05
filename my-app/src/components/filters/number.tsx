import { Slider } from '@/components/ui/slider'
import { FC, useEffect, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import {
  calculateMinimalStep,
  usePropertyValues,
} from '@/components/filters/utils'
import { Loader } from 'lucide-react'

export const NumberFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const [priceRange, setPriceRange] = useState<number[]>([0, 0])

  const { data, isLoading } = usePropertyValues(property.id)

  useEffect(() => {
    if (data) {
      setPriceRange([data!.min!, data!.max!])
    }
  }, [data])

  if (isLoading) {
    return <Loader />
  }

  if (data && typeof data.min === 'number' && typeof data.max === 'number') {
    return (
      <>
        <Slider
          min={data!.min}
          max={data!.max}
          step={calculateMinimalStep(data!.min!, data!.max!)}
          value={priceRange}
          onValueChange={setPriceRange}
          className="mt-2"
        />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{priceRange[0]}</span>
          <span>{priceRange[1]}</span>
        </div>
      </>
    )
  } else {
    return null
  }
}
