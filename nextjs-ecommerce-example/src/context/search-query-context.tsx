import React, {
  createContext,
  useContext,
  useState,
  FC,
  ReactNode,
  useCallback,
} from 'react'
import { Property, PropertyValue, SearchQuery } from '@rushdb/javascript-sdk'

import { processPropertyValue } from '@/components/filters/utils'

type SearchQueryContextType = {
  updateFilter: (property: Property, value: any) => void
  setLabels: (labels: string[]) => void
  clearFilters: (key?: string) => void
  setSkip: (skip: number) => void
  setLimit: (limit: number) => void
  where: SearchQuery['where']
  skip: number
  limit: number
} & SearchQuery

const SearchQueryContext = createContext<SearchQueryContextType | undefined>(
  undefined
)

type ProviderProps = {
  children: ReactNode
  initialWhere?: SearchQuery['where']
  initialLabels?: SearchQuery['labels']
  initialSkip?: number
  initialLimit?: number
}

export const SearchQueryContextProvider: FC<ProviderProps> = ({
  children,
  initialWhere,
  initialLabels,
  initialSkip,
  initialLimit,
}) => {
  const [where, setWhere] = useState<SearchQuery['where']>(initialWhere || {})
  const [labels, setLabels] = useState<SearchQuery['labels']>(
    initialLabels || []
  )
  const [skip, setSkip] = useState(initialSkip ?? 0)
  const [limit, setLimit] = useState(initialLimit ?? 1000)

  const updateFilter = useCallback(
    (property: Property, value: PropertyValue) => {
      const currentState = { ...where }

      if (Array.isArray(value) && value.length === 0) {
        delete (currentState as Record<string, any>)[property.name]
        setWhere(currentState)
      } else {
        setWhere({
          ...currentState,
          [property.name]: processPropertyValue(property, value),
        })
      }
    },
    [where]
  )

  const clearFilters = useCallback(
    (key?: string) => {
      if (typeof key === 'string') {
        const newWhere: SearchQuery['where'] = { ...where }
        console.log(newWhere)

        delete newWhere[key as keyof SearchQuery['where']]

        console.log(newWhere)
        setWhere(newWhere)
      } else {
        setWhere({})
      }
    },
    [where]
  )

  return (
    <SearchQueryContext.Provider
      value={{
        where,
        updateFilter,
        clearFilters,
        labels,
        setLabels,
        skip,
        setSkip,
        limit,
        setLimit,
      }}
    >
      {children}
    </SearchQueryContext.Provider>
  )
}

export const useSearchQuery = (): SearchQueryContextType => {
  const context = useContext(SearchQueryContext)

  if (!context) {
    throw new Error(
      'useFilters must be used within a SearchQueryContextProvider'
    )
  }

  return context
}
