import { Slider } from '@/components/ui/slider'
import { FC, useEffect, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { calculateMinimalStep } from '@/components/filters/utils'
import { Loader } from 'lucide-react'
import { usePropertyValues } from '@/hooks/use-property-values'
import { useOriginalPropertyValues } from '@/hooks/use-original-property-values'

export const NumberFilter: FC<{
  property: Property
  onChange: (value: number[]) => void
  value: { $lte: number; $gte: number }
}> = ({ property, value, onChange }) => {
  const { data, isLoading } = usePropertyValues(property.id)
  const { data: originalData, isLoading: isLoadingOriginal } =
    useOriginalPropertyValues(property.id)

  const [localValue, setLocalValue] = useState<number[]>(
    value ? [value.$gte, value.$lte] : [0, 0]
  )

  useEffect(() => {
    if (value) {
      setLocalValue([value.$gte, value.$lte])
    } else if (originalData) {
      setLocalValue([originalData.min!, originalData.max!])
    } else {
      setLocalValue([0, 0])
    }
  }, [value, originalData])

  if (isLoading || isLoadingOriginal) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader className="h-4 w-4 animate-spin" />
      </div>
    )
  }

  // Use original data for boundaries, but current filtered data for single value logic
  if (
    originalData &&
    typeof originalData.min === 'number' &&
    typeof originalData.max === 'number'
  ) {
    // If min === max, show a tag-like selector instead of a slider
    if (originalData.min === originalData.max) {
      const singleValue = originalData.min
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
          defaultValue={[originalData.min, originalData.max]}
          min={originalData.min}
          max={originalData.max}
          step={calculateMinimalStep(originalData.min, originalData.max)}
          value={localValue}
          onValueChange={setLocalValue}
          onValueCommit={onChange}
          className="mt-2"
        />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{localValue[0]}</span>
          <span>{localValue[1]}</span>
        </div>
        {/* Show current filtered data info if different from original */}
        {data &&
          data.min !== originalData.min &&
          data.max !== originalData.max && (
            <div className="text-xs text-muted-foreground mt-1 text-center">
              Available range: {data.min} - {data.max}
            </div>
          )}
      </>
    )
  } else {
    return null
  }
}
