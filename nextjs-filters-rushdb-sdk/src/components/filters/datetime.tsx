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
import { format } from 'date-fns'
import { Calendar } from '@/components/ui/calendar'
import { useFilters } from '@/context/FiltersContext'

export const DatetimeFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const { filters, updateFilter } = useFilters()
  const { data, isLoading } = usePropertyValues(property.id)

  if (isLoading) {
    return <Loader />
  }

  if (data) {
    const humanizedValue = filters[property.name]?.value
      ? new Date(filters[property.name].value)
      : undefined

    return (
      // @TODO: add support for daterange
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={'outline'}
            className={`w-full justify-start text-left font-normal ${!filters[property.name]?.value && 'text-muted-foreground'}`}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {filters[property.name]?.value ? (
              format(filters[property.name]?.value, 'PPP')
            ) : (
              <span>Pick a date</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          {/* @TODO: allow to pick year from select */}
          <Calendar
            mode="single"
            selected={humanizedValue}
            onSelect={(newValue) => {
              updateFilter(property, newValue ? newValue.toISOString() : null)
            }}
            initialFocus
          />
        </PopoverContent>
      </Popover>
    )
  } else {
    return null
  }
}
