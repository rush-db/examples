import { FC, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { Loader } from 'lucide-react'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { CalendarIcon } from '@radix-ui/react-icons'
import { isValid } from 'date-fns'
import { Calendar } from '@/components/ui/calendar'
import { CalendarPlaceholder } from '@/components/ui/calendar-placeholder'
import { usePropertyValuesLazy } from '@/hooks/use-property-values-lazy'

export const DatetimeFilter: FC<{
  property: Property
  onChange: (value: { from?: string; to?: string }) => void
  value: { $gte?: string; $lte?: string }
}> = ({ property, onChange, value }) => {
  const [isFromOpen, setIsFromOpen] = useState(false)
  const [isToOpen, setIsToOpen] = useState(false)
  const { data: fromData, isLoading: isFromLoading } = usePropertyValuesLazy(
    property.id,
    isFromOpen
  )
  const { data: toData, isLoading: isToLoading } = usePropertyValuesLazy(
    property.id,
    isToOpen
  )

  function applyFromDateFilter(date?: Date | null) {
    if (date && isValid(date)) {
      onChange({
        from: date.toISOString(),
        to: value?.$lte,
      })
    } else {
      onChange({
        from: undefined,
        to: value?.$lte,
      })
    }
  }

  function applyToDateFilter(date?: Date | null) {
    if (date && isValid(date)) {
      onChange({
        from: value?.$gte,
        to: date.toISOString(),
      })
    } else {
      onChange({
        from: value?.$gte,
        to: undefined,
      })
    }
  }

  const fromValue = value?.$gte ? new Date(value.$gte) : undefined
  const toValue = value?.$lte ? new Date(value.$lte) : undefined

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex items-center w-full">
        <span className="text-sm w-12">From:</span>
        <div className="flex-1">
          <Popover open={isFromOpen} onOpenChange={setIsFromOpen}>
            <PopoverTrigger asChild>
              <Button
                variant={'outline'}
                className={`w-full justify-start text-left font-normal ${!fromValue && 'text-muted-foreground'} bg-transparent hover:bg-transparent focus:bg-transparent active:bg-transparent`}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {fromValue ? (
                  <span>{fromValue.toLocaleDateString()}</span>
                ) : (
                  <span>Select date</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              {isFromLoading ? (
                <div className="p-4 flex justify-center">
                  <Loader className="h-4 w-4 animate-spin" />
                </div>
              ) : fromData ? (
                <>
                  <Calendar
                    mode="single"
                    defaultMonth={
                      fromData.min && fromData.max
                        ? new Date(
                            (new Date(fromData.min).getTime() +
                              new Date(fromData.max).getTime()) /
                              2
                          )
                        : new Date()
                    }
                    selected={fromValue}
                    disabled={
                      fromData.min && fromData.max
                        ? {
                            before: new Date(fromData.min),
                            after: new Date(fromData.max),
                          }
                        : undefined
                    }
                    onSelect={applyFromDateFilter}
                    initialFocus
                  />
                  <div className="p-2 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        applyFromDateFilter(null)
                      }}
                    >
                      Reset Date
                    </Button>
                  </div>
                </>
              ) : null}
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <div className="flex items-center w-full">
        <span className="text-sm w-12">To:</span>
        <div className="flex-1">
          <Popover open={isToOpen} onOpenChange={setIsToOpen}>
            <PopoverTrigger asChild>
              <Button
                variant={'outline'}
                className={`w-full justify-start text-left font-normal ${!toValue && 'text-muted-foreground'} bg-transparent hover:bg-transparent focus:bg-transparent active:bg-transparent`}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {toValue ? (
                  <span>{toValue.toLocaleDateString()}</span>
                ) : (
                  <span>Select date</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              {isToLoading ? (
                <div className="p-4 flex justify-center">
                  <Loader className="h-4 w-4 animate-spin" />
                </div>
              ) : toData ? (
                <>
                  <Calendar
                    mode="single"
                    defaultMonth={
                      toData.min && toData.max
                        ? new Date(
                            (new Date(toData.min).getTime() +
                              new Date(toData.max).getTime()) /
                              2
                          )
                        : new Date()
                    }
                    selected={toValue}
                    disabled={
                      toData.min && toData.max
                        ? {
                            before: new Date(toData.min),
                            after: new Date(toData.max),
                          }
                        : undefined
                    }
                    onSelect={applyToDateFilter}
                    initialFocus
                  />
                  <div className="p-2 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        applyToDateFilter(null)
                      }}
                    >
                      Reset Date
                    </Button>
                  </div>
                </>
              ) : null}
            </PopoverContent>
          </Popover>
        </div>
      </div>

      {(fromValue || toValue) && (
        <div className="mt-2 flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              onChange({ from: undefined, to: undefined })
            }}
          >
            Reset All
          </Button>
        </div>
      )}
    </div>
  )
}
