import { FC, useMemo, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { Loader } from 'lucide-react'
import MultipleSelector, { Option } from '@/components/ui/multiple-selector'
import { usePropertyValuesLazy } from '@/hooks/use-property-values-lazy'

export const StringFilter: FC<{
  property: Property
  onChange: (value: string[]) => void
  value: { $in: string[] } | { $contains: string }
}> = ({ property, value, onChange }) => {
  const [searchValue, setSearchValue] = useState<string | undefined>()
  const [isOpen, setIsOpen] = useState(false)
  const { data, isLoading, refetch } = usePropertyValuesLazy(
    property.id,
    isOpen, // Only fetch when dropdown is open
    searchValue
  )

  const getValue = (value: { $in: string[] } | { $contains: string }) => {
    if (value) {
      return (
        '$in' in value ? value.$in : '$contains' in value ? [value] : []
      ) as string[]
    }
    return []
  }

  const mapOption = (value: string) => ({
    label: value,
    value: value,
  })

  const pickValue = (option: Option) => option.value

  const options = useMemo(
    () => ((data?.values ?? []) as string[]).map(mapOption),
    [data]
  )

  return (
    <>
      <div className="space-y-2">
        <MultipleSelector
          options={options}
          value={getValue(value).map(mapOption)}
          onChange={(newValue) => {
            onChange(newValue.map(pickValue))
            setSearchValue(undefined)
          }}
          inputProps={{
            onValueChange: (value) => {
              if (value) {
                setSearchValue(value)
              } else {
                setSearchValue(undefined)
              }
            },
            onFocus: () => {
              setIsOpen(true)
            },
            onBlur: () => {
              setIsOpen(false)
            },
          }}
          placeholder="Pick options..."
          emptyIndicator={
            isLoading && isOpen ? (
              <div className="flex items-center justify-center p-4">
                <Loader className="h-4 w-4 animate-spin" />
              </div>
            ) : !isLoading && options.length === 0 ? (
              <p className="text-center text-lg leading-10 text-muted-foreground">
                no results found.
              </p>
            ) : undefined
          }
        />
      </div>
    </>
  )
}
