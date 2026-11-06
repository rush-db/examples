import { useState, useEffect } from 'react'
import { SearchField } from '@/components/search-field'
import { useSearch } from '@/hooks/use-search'
import { useDebounce } from '@/hooks/use-debounce'
import {
  DBRecordInstance,
  DBRecordsArrayInstance,
} from '@rushdb/javascript-sdk'

// This context will be used to share search state between SearchField and RecordsGrid
import { createContext, useContext } from 'react'

type SearchSettings = {
  vectorDimension: number
}

type SearchContextType = {
  searchText: string
  setSearchText: (text: string) => void
  searchResults?: DBRecordsArrayInstance<any>
  isSearching: boolean
  isSearchEnabled: boolean
  searchSettings: SearchSettings
  updateSearchSettings: (settings: Partial<SearchSettings>) => void
}

const SearchContext = createContext<SearchContextType | undefined>(undefined)

interface SearchProviderProps {
  children: React.ReactNode
  initialEnabled?: boolean
}

export const SearchProvider = ({
  children,
  initialEnabled,
}: SearchProviderProps) => {
  const [searchText, setSearchText] = useState('')
  const [searchSettings, setSearchSettings] = useState<SearchSettings>({
    vectorDimension: 384,
  })

  const debouncedSearchText = useDebounce(searchText, 300)
  const {
    data: searchResults,
    isLoading,
    isFetching,
  } = useSearch(debouncedSearchText, searchSettings)

  // Check if search is enabled by checking for BACKEND_URL
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL
  const isSearchEnabled =
    (typeof backendUrl === 'string' && backendUrl.length > 0) ||
    !!initialEnabled

  const isSearching = isLoading || isFetching

  const updateSearchSettings = (settings: Partial<SearchSettings>) => {
    setSearchSettings((prev) => ({ ...prev, ...settings }))
  }

  return (
    <SearchContext.Provider
      value={{
        searchText,
        setSearchText,
        searchResults,
        isSearching,
        isSearchEnabled,
        searchSettings,
        updateSearchSettings,
      }}
    >
      {children}
    </SearchContext.Provider>
  )
}

export const useSearchContext = () => {
  const context = useContext(SearchContext)
  if (!context) {
    throw new Error('useSearchContext must be used within a SearchProvider')
  }
  return context
}
