import { Search, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useSearchContext } from '@/context/search-context'

export function SearchField() {
  const { searchText, setSearchText, searchResults, isSearching } =
    useSearchContext()

  const handleClearSearch = () => {
    setSearchText('')
  }

  return (
    <div className="flex-1 max-w-md">
      <div className="relative search-container">
        <Search className="search-icon w-4 h-4" />
        <Input
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="Search records..."
          className="search-input pl-10 pr-10 h-10"
        />
        {isSearching ? (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground animate-spin" />
        ) : searchText ? (
          <Button
            variant="ghost"
            size="sm"
            className="search-clear h-6 w-6 p-0"
            onClick={handleClearSearch}
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </Button>
        ) : null}
      </div>
      {searchText && !isSearching && (
        <div className="text-xs text-muted-foreground mt-1">
          {searchResults?.total || 0} results found
        </div>
      )}
    </div>
  )
}
