import { ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useRecords } from '@/hooks/use-records'
import { useSearchQuery } from '@/context/search-query-context'
import { useDeleteAllRecords } from '@/hooks/use-delete-all-records'

const ITEMS_PER_PAGE_OPTIONS = [50, 100, 500, 1000]

export function ControlPanel() {
  const deleteAllRecords = useDeleteAllRecords()

  const { data: records, isLoading, isFetching } = useRecords()
  const { skip, limit, setSkip, setLimit } = useSearchQuery()

  const totalPages = records?.total ? Math.ceil(records.total / limit) : 1
  const currentPage = skip / limit + 1

  const handlePrevPage = () => {
    if (skip > 0) setSkip(skip - limit)
  }

  const handleNextPage = () => {
    if (records?.total && skip + limit < records?.total) {
      setSkip(skip + limit)
    }
  }

  const handleLimitChange = (newLimit: string) => {
    setLimit(Number(newLimit))
    setSkip(0) // Reset to first page when changing limit
  }

  if (records) {
    return (
      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2">
        <div className="flex items-center gap-4 px-6 py-3 bg-background/80 backdrop-blur-sm border rounded-full shadow-lg">
          <Button
            variant="outline"
            size="icon"
            className="rounded-full"
            onClick={handlePrevPage}
            disabled={skip === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              Page {currentPage} of {totalPages}
            </span>
          </div>
          <Button
            variant="outline"
            size="icon"
            className="rounded-full"
            onClick={handleNextPage}
            disabled={skip + limit >= records.total!}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <div className="h-6 w-px bg-border mx-2" />
          <Select value={String(limit)} onValueChange={handleLimitChange}>
            <SelectTrigger className="w-[100px]">
              <SelectValue placeholder="Items per page" />
            </SelectTrigger>
            <SelectContent>
              {ITEMS_PER_PAGE_OPTIONS.map((value) => (
                <SelectItem key={value} value={String(value)}>
                  {value} per page
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="h-6 w-px bg-border mx-2" />
          <Button
            variant="destructive"
            size="sm"
            className="rounded-full"
            onClick={() => deleteAllRecords.mutateAsync()}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete All
          </Button>
        </div>
      </div>
    )
  }
  return null
}
