import React, {
  createContext,
  useContext,
  useState,
  FC,
  ReactNode,
  useCallback,
} from 'react'
import { Property } from '@rushdb/javascript-sdk'

type FilterState = {
  [property: Property['name']]: {
    type: Property['type']
    value: any
  }
}

type FiltersContextType = {
  filters: FilterState
  updateFilter: (property: Property, value: any) => void
  clearFilters: () => void
}

const FiltersContext = createContext<FiltersContextType | undefined>(undefined)

export const FiltersProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [filters, setFilters] = useState<FilterState>({})

  const updateFilter = useCallback((property: Property, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [property.name]: {
        type: property.type,
        value,
      },
    }))
  }, [])

  const clearFilters = useCallback(() => setFilters({}), [])

  return (
    <FiltersContext.Provider value={{ filters, updateFilter, clearFilters }}>
      {children}
    </FiltersContext.Provider>
  )
}

export const useFilters = (): FiltersContextType => {
  const context = useContext(FiltersContext)

  if (!context) {
    throw new Error('useFilters must be used within a FiltersProvider')
  }

  return context
}
