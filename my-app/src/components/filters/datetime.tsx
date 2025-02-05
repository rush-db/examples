import { FC, useState } from 'react'
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

export const DatetimeFilter: FC<{ property: Property }> = ({
  property,
}: {
  property: Property
}) => {
  const [date, setDate] = useState<Date>()

  const { data, isLoading } = usePropertyValues(property.id)

  if (isLoading) {
    return <Loader />
  }

  if (data) {
    return (
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
          <Calendar
            mode="single"
            selected={date}
            onSelect={setDate}
            initialFocus
          />
        </PopoverContent>
      </Popover>
    )
  } else {
    return null
  }
}
