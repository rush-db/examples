import { FC, useEffect, useState } from 'react'
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
  const [date, setDate] = useState<Date>(
    filters[property.name]?.value || undefined
  )
  const [isDirty, setIsDirty] = useState(false)

  const { data, isLoading } = usePropertyValues(property.id)

  useEffect(() => {
    if (isDirty) {
      updateFilter(property, date ? date.toISOString() : null)
    }
  }, [date, property, updateFilter, isDirty])

  if (isLoading) {
    return <Loader />
  }

  if (data) {
    return (
      // @TODO: add support for daterange
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={'outline'}
            className={`w-full justify-start text-left font-normal ${!date && 'text-muted-foreground'}`}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date ? format(date, 'PPP') : <span>Pick a date</span>}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          {/* @TODO: allow to pick year from select */}
          <Calendar
            mode="single"
            selected={date}
            onSelect={(newValue) => {
              setDate(newValue)
              setIsDirty(true)
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
