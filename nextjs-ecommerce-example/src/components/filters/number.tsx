import { Slider } from '@/components/ui/slider'
import { FC, useEffect, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { calculateMinimalStep } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { useSearchQuery } from '@/context/search-query-context'
import { usePropertyValues } from '@/hooks/use-property-values'
import { useOriginalPropertyValues } from '@/hooks/use-original-property-values'

export const NumberFilter: FC<{
  property: Property
  onChange: (value: number[]) => void
  value: { $lte: number; $gte: number }
}> = ({ property, value, onChange }) => {
  const { where } = useSearchQuery()
  const { data, isLoading } = usePropertyValues(property.id)
  const { data: originalData, isLoading: isLoadingOriginal } =
    useOriginalPropertyValues(property.id)

  const [stableRange, setStableRange] = useState<{
    min: number
    max: number
  } | null>(null)

  const [localValue, setLocalValue] = useState<number[]>(
    value ? [value.$gte, value.$lte] : [0, 0]
  )

  useEffect(() => {
    if (!stableRange) {
      if (
        data &&
        typeof data.min === 'number' &&
        typeof data.max === 'number'
      ) {
        setStableRange({ min: data.min, max: data.max })
      } else if (
        originalData &&
        typeof originalData.min === 'number' &&
        typeof originalData.max === 'number'
      ) {
        setStableRange({ min: originalData.min, max: originalData.max })
      }
    }
  }, [stableRange, data, originalData])

  useEffect(() => {
    if (value) {
      setLocalValue([value.$gte, value.$lte])
    } else if (stableRange) {
      setLocalValue([stableRange.min!, stableRange.max!])
    } else {
      setLocalValue([0, 0])
    }
  }, [value, stableRange])

  if (isLoading || isLoadingOriginal) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader className="h-4 w-4 animate-spin" />
      </div>
    )
  }

  const range = stableRange ?? data ?? originalData

  if (range && typeof range.min === 'number' && typeof range.max === 'number') {
    // If min === max, show a tag-like selector instead of a slider
    if (range.min === range.max) {
      const singleValue = range.min
      const isSelected =
        value && value.$gte === singleValue && value.$lte === singleValue

      return (
        <button
          onClick={() => {
            if (isSelected) {
              // Deselect by passing an empty array (this will be handled by parent component)
              onChange([])
            } else {
              // Select the single value
              onChange([singleValue, singleValue])
            }
          }}
          className={`px-3 py-1 rounded-full text-sm transition-colors ${
            isSelected
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          }`}
        >
          {singleValue}
        </button>
      )
    }

    return (
      <>
        <Slider
          defaultValue={[range.min, range.max]}
          min={range.min}
          max={range.max}
          step={calculateMinimalStep(range.min, range.max)}
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
