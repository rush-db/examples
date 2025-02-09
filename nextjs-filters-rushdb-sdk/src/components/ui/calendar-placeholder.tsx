import React from 'react'
import { format } from 'date-fns'

export type DateRange = {
  from?: Date | string
  to?: Date | string
}

export const CalendarPlaceholder: React.FC<{ range?: DateRange }> = ({
  range,
}) => {
  if (!range || !range.from) {
    return <span>Pick a date</span>
  }
  if (!range.to) {
    return <span>Please pick a second date</span>
  }

  const fromDate =
    range.from instanceof Date ? range.from : new Date(range.from)
  const toDate = range.to instanceof Date ? range.to : new Date(range.to)

  return (
    <span>
      {format(fromDate, 'PPP')} - {format(toDate, 'PPP')}
    </span>
  )
}
