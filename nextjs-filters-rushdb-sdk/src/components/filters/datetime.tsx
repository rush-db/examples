import { FC } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { usePropertyValues } from '@/components/filters/utils'
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
import { useFilters } from '@/context/filter-context'
import { CalendarPlaceholder } from '@/components/ui/calendar-placeholder'

export const DatetimeFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const { filters, updateFilter } = useFilters()
  const { data, isLoading } = usePropertyValues(property.id)

  function applyDateFilter(range: { from?: Date; to?: Date }) {
    if (range && (range.from || range.to)) {
      const isFromValid = isValid(range.from)
      const isToValid = isValid(range.to)
      const toDateString = isValid(range.to)
        ? range.to?.toISOString()
        : undefined
      const fromDateString = isFromValid ? range.from?.toISOString() : undefined

      updateFilter(property, {
        from: isFromValid ? fromDateString : toDateString,
        to: isToValid ? (isFromValid ? toDateString : undefined) : undefined,
      })
    } else {
      updateFilter(property, { from: undefined, to: undefined })
    }
  }

  if (isLoading) {
    return <Loader />
  }

  if (data) {
    const rangeValue = filters[property.name]?.value
      ? {
          from: filters[property.name].value.from,
          to: filters[property.name].value.to,
        }
      : undefined

    const humanizedValue = rangeValue
      ? {
          from: new Date(rangeValue.from),
          to: rangeValue.to ? new Date(rangeValue.to) : undefined,
        }
      : undefined

    const defaultMonth = new Date(
      (new Date(data.min).getTime() + new Date(data.max).getTime()) / 2
    )

    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={'outline'}
            className={`w-full justify-start text-left font-normal ${!filters[property.name]?.value && 'text-muted-foreground'}`}
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
              before: new Date(data.min),
              after: new Date(data.max),
            }}
            onSelect={applyDateFilter}
            initialFocus
          />
          <div className="p-2 flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                updateFilter(property, { from: undefined, to: undefined })
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
