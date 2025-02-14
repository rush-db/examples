import { FC } from 'react'
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
import { usePropertyValues } from '@/hooks/use-property-values'

export const DatetimeFilter: FC<{
  property: Property
  onChange: (value: { from?: string; to?: string }) => void
  value: { $gte?: string; $lte?: string }
}> = ({ property, onChange, value }) => {
  const { data, isLoading } = usePropertyValues(property.id)

  function applyDateFilter(range?: { from?: Date; to?: Date }) {
    if (range && (range.from || range.to)) {
      const isFromValid = isValid(range.from)
      const isToValid = isValid(range.to)
      const toDateString = isValid(range.to)
        ? range.to?.toISOString()
        : undefined

      const fromDateString = isFromValid ? range.from?.toISOString() : undefined

      onChange({
        from: isFromValid ? fromDateString : toDateString,
        to: isToValid ? (isFromValid ? toDateString : undefined) : undefined,
      })
    } else {
      onChange({ from: undefined, to: undefined })
    }
  }

  if (isLoading) {
    return <Loader />
  }

  if (data) {
    const rangeValue = value
      ? {
          from: value.$gte,
          to: value.$lte,
        }
      : undefined

    const humanizedValue = rangeValue
      ? {
          from: new Date(rangeValue.from!),
          to: rangeValue.to ? new Date(rangeValue.to) : undefined,
        }
      : undefined

    const defaultMonth = new Date(
      (new Date(data.min!).getTime() + new Date(data.max!).getTime()) / 2
    )

    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={'outline'}
            className={`w-full justify-start text-left font-normal ${!value && 'text-muted-foreground'}`}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            <CalendarPlaceholder range={rangeValue} />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            defaultMonth={defaultMonth}
            selected={humanizedValue}
            disabled={{
              before: new Date(data.min!),
              after: new Date(data.max!),
            }}
            onSelect={applyDateFilter}
            initialFocus
          />
          <div className="p-2 flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                onChange({ from: undefined, to: undefined })
              }}
            >
              Reset Date
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    )
  } else {
    return null
  }
}
