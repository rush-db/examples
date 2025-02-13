import { FC, useEffect, useMemo, useState } from 'react'
import { Property } from '@rushdb/javascript-sdk'
import { Loader } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import MultipleSelector, { Option } from '@/components/ui/multiple-selector'
import { usePropertyValues } from '@/hooks/use-property-values'

export const StringFilter: FC<{
  property: Property
  onChange: (value: string[]) => void
  value: { $in: string[] } | { $contains: string }
}> = ({ property, value, onChange }) => {
  const [searchValue, setSearchValue] = useState<string | undefined>()
  const { data, isLoading, refetch } = usePropertyValues(
    property.id,
    searchValue
  )

  useEffect(() => {
    console.log(data)
  }, [data])

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

  if (isLoading) {
    return <Loader />
  }
  return (
    <>
      <div className="space-y-2">
        <MultipleSelector
          defaultOptions={options}
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
          }}
          placeholder="Pick options..."
          emptyIndicator={
            <p className="text-center text-lg leading-10 text-gray-600 dark:text-gray-400">
              no results found.
            </p>
          }
        />
        {/*{(data.values as string[]).map((category) => (*/}
        {/*  <div key={category} className="flex items-center space-x-2">*/}
        {/*    <Checkbox*/}
        {/*      id={category}*/}
        {/*      checked={getValue(value).includes(category)}*/}
        {/*      onCheckedChange={(checked) => {*/}
        {/*        const newValue = checked*/}
        {/*          ? [...(getValue(value) || []), category]*/}
        {/*          : (getValue(value) || []).filter((c) => c !== category)*/}

        {/*        onChange(newValue)*/}
        {/*      }}*/}
        {/*    />*/}
        {/*    <Label htmlFor={category}>{category}</Label>*/}
        {/*  </div>*/}
        {/*))}*/}
      </div>
    </>
  )
}
