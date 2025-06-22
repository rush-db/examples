'use client'

import { useEffect, useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RecordModal } from '@/components/record-modal'
import { useRecords } from '@/hooks/use-records'
import { useLabelColors } from '@/hooks/use-label-colors'
import { Label } from '@/components/labels/label'
import { ThemeToggle } from '@/components/theme-toggle'
import { Loader, Calendar, Eye } from 'lucide-react'
import { DBRecordInstance } from '@rushdb/javascript-sdk'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/context/sidebar-context'
import { useSearchContext } from '@/context/search-context'

export default function RecordsGrid() {
  const [currentRecord, setCurrentRecord] = useState<
    DBRecordInstance | undefined
  >()

  const sidebarContext = useSidebar()
  const { searchText, searchResults, isSearching, isSearchEnabled } =
    useSearchContext()

  // Use regular records when no search is active
  const { data: records, isLoading, isFetching } = useRecords()

  // Determine which data source to use
  const isSearchActive = isSearchEnabled && !!searchText.trim()
  const activeRecords = isSearchActive ? searchResults : records
  const isActiveLoading = isSearchActive ? isSearching : isLoading || isFetching
  const { getLabelColor } = useLabelColors()

  if (isActiveLoading) {
    return (
      <div className="flex-1 p-6 overflow-auto">
        <div className="mb-8">
          <div className="h-8 bg-muted rounded w-32 animate-pulse mb-2"></div>
          <div className="h-4 bg-muted rounded w-48 animate-pulse"></div>
        </div>
        <div
          className={cn(
            'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6',
            { 'grid-cols-3!': sidebarContext?.rightSidebarOpen }
          )}
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <Card
              key={i}
              className="animate-pulse border border-border shadow-sm bg-card"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="h-6 bg-muted rounded-full w-20"></div>
                  <div className="h-4 bg-muted rounded w-12"></div>
                </div>
              </CardHeader>
              <CardContent className="px-6 pb-4">
                <div className="space-y-3">
                  <div className="h-4 bg-muted rounded w-full"></div>
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="pt-2 border-t border-border">
                    <div className="h-3 bg-muted rounded w-1/2"></div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-0 px-6 pb-6">
                <div className="h-9 bg-muted rounded w-full"></div>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6">
      {/* Header Section */}

      {/* Records Grid */}
      <div
        className={cn(
          'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6',
          { 'lg:grid-cols-3': sidebarContext?.rightSidebarOpen }
        )}
      >
        {activeRecords?.data?.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              {isSearchActive ? 'No search results found' : 'No records found'}
            </h3>
            <p className="text-muted-foreground max-w-sm">
              {isSearchActive
                ? 'Try adjusting your search query or filters.'
                : 'Try adjusting your filters or check back later for new records.'}
            </p>
          </div>
        ) : (
          activeRecords?.data?.map((record: DBRecordInstance) => (
            <Card
              key={record.id()}
              className="group transition-all duration-200 border border-border bg-card shadow-sm hover:shadow-md hover:border-foreground/20"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <Label
                    variant={getLabelColor(record.label()) as any}
                    active={false}
                    className="w-fit"
                  >
                    {record.label()}
                  </Label>
                  <div className="text-xs text-muted-foreground font-mono opacity-60">
                    #{record.id().slice(-6)}
                  </div>
                </div>
              </CardHeader>

              <CardContent className="px-6 pb-4">
                <div className="space-y-3">
                  {/* Main content area */}
                  <div className="min-h-[60px] flex items-center">
                    {record.data.thumbnail ? (
                      <img
                        src={record.data.thumbnail as string}
                        className="w-16 h-16 rounded mr-3 object-cover"
                      />
                    ) : null}
                    {record.data.title ? (
                      <div className="flex flex-col">
                        <p>{record.data.title}</p>
                        <p className="text-sm text-muted-foreground italic">
                          {(record.data.description as string)?.slice(0, 50) +
                            '...' ||
                            'No description available for this record.'}
                        </p>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        Use the button below to explore this record's details
                        and relationships
                      </p>
                    )}
                  </div>

                  {/* Metadata */}
                  <div className="pt-2 border-t border-border">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        Created
                      </span>
                      <span className="font-mono">
                        {new Date(record.date()).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>

              <CardFooter className="pt-0 px-6 pb-6">
                <Button
                  onClick={() => setCurrentRecord(record)}
                  className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                  variant="outline"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  View Details
                </Button>
              </CardFooter>
            </Card>
          ))
        )}
      </div>
      {currentRecord && (
        <RecordModal
          record={currentRecord}
          isOpen={!!currentRecord}
          onClose={() => setCurrentRecord(undefined)}
        />
      )}
    </div>
  )
}
