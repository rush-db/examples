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
import React, { useMemo } from 'react'
import {
  Filter,
  Tag,
  X,
  Hash,
  Type,
  Calendar,
  ToggleLeft,
  ExternalLink,
  FileText,
  Github,
  Globe,
} from 'lucide-react'
import { Logo } from './logo'
import { ThemeToggle } from '@/components/theme-toggle'

export function FiltersSidebar() {
  const { clearFilters, where = {}, updateFilter } = useSearchQuery()
  const properties = useProperties()

  const hasAnyFiltersApplied = useMemo(
    () => Boolean(Object.keys(where).length),
    [where]
  )

  const getPropertyIcon = (type: string) => {
    switch (type) {
      case 'number':
        return <Hash className="w-3.5 h-3.5" />
      case 'string':
        return <Type className="w-3.5 h-3.5" />
      case 'boolean':
        return <ToggleLeft className="w-3.5 h-3.5" />
      case 'datetime':
        return <Calendar className="w-3.5 h-3.5" />
      default:
        return <Filter className="w-3.5 h-3.5" />
    }
  }

  const getPropertyColor = (type: string) => {
    switch (type) {
      case 'number':
        return 'text-orange-500'
      case 'string':
        return 'text-green-500'
      case 'boolean':
        return 'text-purple-500'
      case 'datetime':
        return 'text-amber-500'
      default:
        return 'text-muted-foreground'
    }
  }

  const renderPropertyFilter = (property: any) => {
    const hasValue = typeof pickValue(where, property.name) !== 'undefined'

    const filterContent = () => {
      switch (property.type) {
        case 'number':
          return (
            <NumberFilter
              property={property}
              value={pickValue(where, property.name)}
              onChange={(value) => updateFilter(property, value)}
            />
          )
        case 'string':
          return (
            <StringFilter
              property={property}
              value={pickValue(where, property.name)}
              onChange={(value) => updateFilter(property, value)}
            />
          )
        case 'boolean':
          return (
            <BooleanFilter
              property={property}
              value={pickValue(where, property.name)}
              onChange={(value) => updateFilter(property, value)}
            />
          )
        case 'datetime':
          return (
            <DatetimeFilter
              property={property}
              value={pickValue<{
                $gte: string
                $lte: string
              }>(where, property.name)}
              onChange={(range) => updateFilter(property, range)}
            />
          )
        default:
          return null
      }
    }

    return (
      <div
        key={property.id}
        className="bg-card rounded-lg border border-border transition-all duration-200 hover:border-border hover:bg-card"
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div
                className={`${getPropertyColor(property.type)} flex-shrink-0`}
              >
                {getPropertyIcon(property.type)}
              </div>
              <span className="text-sm font-medium text-foreground">
                {property.name}
              </span>
            </div>
            {hasValue && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => clearFilters(property.name)}
                className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              >
                <X className="w-3 h-3" />
              </Button>
            )}
          </div>
          {filterContent()}
        </div>
      </div>
    )
  }

  return (
    <div className="w-80 bg-gradient-to-b from-background to-muted/20 border-r border-border/50 space-y-6 overflow-y-auto h-full shadow-sm custom-scrollbar fixed">
      {/* Header */}
      <div className="bg-background/95 backdrop-blur-sm border-b border-border/50">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <Logo />
            <div className="h-6 w-px bg-border"></div>
            <div className="flex items-center justify-between w-full">
              <div>
                <h1 className="text-lg font-semibold text-foreground">
                  RushDB
                </h1>
                <p className="text-xs text-muted-foreground">
                  Demo Application
                </p>
              </div>
              <ThemeToggle />
            </div>
          </div>

          {/* Links Section */}
          <div className="flex flex-col gap-2 mt-4">
            <a
              href="https://rushdb.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors group"
            >
              <Globe className="w-3 h-3" />
              <span>RushDB Website</span>
              <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
            <a
              href="https://docs.rushdb.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 texts-sm text-muted-foreground hover:text-foreground transition-colors group"
            >
              <FileText className="w-3 h-3" />
              <span>Official Documentation</span>
              <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
            <a
              href="https://github.com/rush-db/examples/tree/main/nextjs-filters-rushdb-sdk"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors group"
            >
              <Github className="w-3 h-3" />
              <span>View Source Code</span>
              <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
          </div>
        </div>
      </div>

      <div className="px-6 space-y-6 pb-6">
        {/* Labels Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded-md">
              <Tag className="w-4 h-4 text-primary" />
            </div>
            <div>
              <span className="text-sm font-semibold text-foreground">
                Labels
              </span>
              <p className="text-xs text-muted-foreground">
                Dynamic categorization
              </p>
            </div>
          </div>
          <LabelsSelect />
        </div>

        {/* Property Filters Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded-md">
              <Filter className="w-4 h-4 text-primary" />
            </div>
            <div>
              <span className="text-sm font-semibold text-foreground">
                Property Filters
              </span>
              <p className="text-xs text-muted-foreground">
                Dynamic property filtering
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {properties.isLoading ? (
              // Loading skeleton for filters
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="bg-card rounded-lg border border-border p-4 animate-pulse"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-muted rounded"></div>
                        <div className="h-4 bg-muted rounded w-20"></div>
                      </div>
                    </div>
                    <div className="h-9 bg-muted rounded"></div>
                  </div>
                ))}
              </div>
            ) : (
              properties.data?.map(renderPropertyFilter)
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
