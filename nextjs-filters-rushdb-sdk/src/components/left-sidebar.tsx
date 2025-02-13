'use client'

import { NumberFilter } from '@/components/filters/number'
import { StringFilter } from '@/components/filters/string'
import { BooleanFilter } from '@/components/filters/boolean'
import { DatetimeFilter } from '@/components/filters/datetime'
import { Button } from '@/components/ui/button'
import { useSearchQuery } from '@/context/search-query-context'
import { useProperties } from '@/hooks/use-properties'
import { LabelsSelect } from '@/components/labels/labels-select'

import { pickValue } from '@/components/filters/utils'
import { Logo } from '@/components/logo'
import { useMemo } from 'react'

export default function LeftSidebar() {
  const { clearFilters, where = {}, updateFilter } = useSearchQuery()
  const properties = useProperties()

  const hasAnyFiltersApplied = useMemo(
    () => Boolean(Object.keys(where).length),
    [where]
  )

  return (
    <div className="w-80 bg-background border-r space-y-4 overflow-y-auto h-screen fixed pb-32">
      <div className="border-b">
        <div className="p-4 flex items-center justify-between">
          <Logo />
          <h1 className="text-2xl font-bold">RushDB Demo App</h1>
        </div>
      </div>
      <div className="border-b">
        <div className="px-4 pb-4">
          <h2 className="text-xl font-bold">Labels</h2>
          <p className="text-xs text-gray-500 mb-4">
            [Dynamically assigned from any input data]
          </p>
          <LabelsSelect />
        </div>
      </div>

      <div className="px-4">
        <h2 className="text-xl font-bold">Filters</h2>
        <p className="text-xs text-gray-500">
          [Dynamically built from any input data]
        </p>
        {hasAnyFiltersApplied ? (
          <Button
            className="mt-4 "
            variant="outline"
            size="sm"
            onClick={() => clearFilters()}
          >
            Reset Filters
          </Button>
        ) : null}
      </div>

      {properties.data?.map((property) => {
        switch (property.type) {
          case 'number': {
            return (
              <div className="border-b" key={property.id}>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <p className="capitalize mb-2">{property.name}</p>

                    {typeof pickValue(where, property.name) !== 'undefined' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => clearFilters(property.name)}
                      >
                        Clear
                      </Button>
                    ) : null}
                  </div>
                  <NumberFilter
                    property={property}
                    value={pickValue(where, property.name)}
                    onChange={(value) => updateFilter(property, value)}
                  />
                </div>
              </div>
            )
          }
          case 'string': {
            return (
              <div className="border-b" key={property.id}>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <p className="capitalize mb-2">{property.name}</p>

                    {typeof pickValue(where, property.name) !== 'undefined' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => clearFilters(property.name)}
                      >
                        Clear
                      </Button>
                    ) : null}
                  </div>
                  <StringFilter
                    property={property}
                    value={pickValue(where, property.name)}
                    onChange={(value) => updateFilter(property, value)}
                  />
                </div>
              </div>
            )
          }
          case 'boolean': {
            return (
              <div className="border-b" key={property.id}>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <p className="capitalize mb-2">{property.name}</p>

                    {typeof pickValue(where, property.name) !== 'undefined' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => clearFilters(property.name)}
                      >
                        Clear
                      </Button>
                    ) : null}
                  </div>
                  <BooleanFilter
                    property={property}
                    value={pickValue(where, property.name)}
                    onChange={(value) => updateFilter(property, value)}
                  />
                </div>
              </div>
            )
          }
          case 'datetime': {
            return (
              <div className="border-b" key={property.id}>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <p className="capitalize mb-2">{property.name}</p>

                    {typeof pickValue(where, property.name) !== 'undefined' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => clearFilters(property.name)}
                      >
                        Clear
                      </Button>
                    ) : null}
                  </div>
                  <DatetimeFilter
                    property={property}
                    value={pickValue<{
                      from: string
                      to: string
                    }>(where, property.name)}
                    onChange={(range) => updateFilter(property, range)}
                  />
                </div>
              </div>
            )
          }
          default: {
            break
          }
        }
      })}
    </div>
  )
}
