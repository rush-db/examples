'use client'

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { SearchQuery } from '@rushdb/javascript-sdk'
import { useQuery } from '@tanstack/react-query'
import { db } from '@/db'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NumberFilter } from '@/components/filters/number'
import { StringFilter } from '@/components/filters/string'
import { BooleanFilter } from '@/components/filters/boolean'
import { DatetimeFilter } from '@/components/filters/datetime'
import { Button } from '@/components/ui/button'
import { useFilters } from '@/context/filter-context'

function useProperties(query: SearchQuery = {}) {
  return useQuery({
    queryKey: ['properties', query],
    queryFn: () => db.properties.find(query),
    select: (data) => {
      return data.data
    },
  })
}

export default function LeftSidebar() {
  const properties = useProperties()
  const { clearFilters } = useFilters()

  return (
    <div className="w-64 bg-background border-r p-4 space-y-4 overflow-y-auto h-screen fixed mt-[77px]">
      <h2 className="text-xl font-bold">Filters</h2>
      <p className="text-xs text-gray-500 mb-4">
        [Dynamically built from any input data]
      </p>

      <Button
        className="mt-4"
        variant="outline"
        size="sm"
        onClick={clearFilters}
      >
        Reset Filters
      </Button>

      <hr />

      <ScrollArea>
        <Accordion type="single" collapsible className="w-full">
          {properties.data?.map((property) => {
            switch (property.type) {
              case 'number': {
                return (
                  <AccordionItem
                    value={property.name + property.type}
                    key={property.id}
                  >
                    <AccordionTrigger>
                      <p className="capitalize">{property.name}</p>
                    </AccordionTrigger>
                    <AccordionContent>
                      <NumberFilter property={property} />
                    </AccordionContent>
                  </AccordionItem>
                )
              }
              case 'string': {
                return (
                  <AccordionItem
                    value={property.name + property.type}
                    key={property.id}
                  >
                    <AccordionTrigger>
                      <p className="capitalize">{property.name}</p>
                    </AccordionTrigger>
                    <AccordionContent>
                      <StringFilter property={property} />
                    </AccordionContent>
                  </AccordionItem>
                )
              }
              case 'boolean': {
                return (
                  <AccordionItem
                    value={property.name + property.type}
                    key={property.id}
                  >
                    <AccordionTrigger>
                      <p className="capitalize">{property.name}</p>
                    </AccordionTrigger>
                    <AccordionContent>
                      <BooleanFilter property={property} />
                    </AccordionContent>
                  </AccordionItem>
                )
              }
              case 'datetime': {
                return (
                  <AccordionItem
                    value={property.name + property.type}
                    key={property.id}
                  >
                    <AccordionTrigger>
                      <p className="capitalize">{property.name}</p>
                    </AccordionTrigger>
                    <AccordionContent>
                      <DatetimeFilter property={property} />
                    </AccordionContent>
                  </AccordionItem>
                )
              }
              default: {
                break
              }
            }
          })}
        </Accordion>
      </ScrollArea>
    </div>
  )
}
