import { Slider } from '@/components/ui/slider'
import { FC, useEffect, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { calculateMinimalStep } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { usePropertyValues } from '@/hooks/use-property-values'

export const NumberFilter: FC<{
  property: Property
  onChange: (value: number[]) => void
  value: { $lte: number; $gte: number }
}> = ({ property, value, onChange }) => {
  const { data, isLoading } = usePropertyValues(property.id)

  const [localValue, setLocalValue] = useState<number[]>(
    value ? [value.$gte, value.$lte] : [0, 0]
  )

  useEffect(() => {
    setLocalValue(
      value ? [value.$gte, value.$lte] : data ? [data.min!, data.max!] : [0, 0]
    )
  }, [value, data])

  if (isLoading) {
    return <Loader />
  }

  if (data && typeof data.min === 'number' && typeof data.max === 'number') {
    return (
      <>
        <Slider
          defaultValue={[data.min, data.max]}
          min={data.min}
          max={data.max}
          step={calculateMinimalStep(data.min, data.max)}
          value={localValue}
          onValueChange={setLocalValue}
          onValueCommit={onChange}
          className="mt-2"
        />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{localValue[0]}</span>
          <span>{localValue[1]}</span>
        </div>
      </>
    )
  } else {
    return null
  }
}
