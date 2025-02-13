import { useLabels } from '@/hooks/use-labels'
import { useSearchQuery } from '@/context/search-query-context'
import { Label } from '@/components/labels/label'

export function LabelsSelect() {
  const { data, isLoading } = useLabels()
  const { labels = [], setLabels } = useSearchQuery()

  const toggleTag = (tag: string) => {
    setLabels(
      labels?.includes(tag) ? labels.filter((t) => t !== tag) : [...labels, tag]
    )
  }

  if (!data && isLoading) {
    return null
  }

  return (
    <div className="flex flex-wrap gap-2">
      {data?.map(({ color, label, value }) => (
        <Label
          active={labels.includes(label)}
          variant={color}
          onClick={() => toggleTag(label)}
          quantity={value}
        >
          {label}
        </Label>
      ))}
    </div>
  )
}
