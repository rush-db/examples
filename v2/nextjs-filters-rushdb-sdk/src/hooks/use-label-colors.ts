import { useCallback } from 'react'
import { getFromIndex } from '@/components/labels/utils'
import { labelVariants } from '@/components/labels/constants'
import { useLabels } from './use-labels'

/**
 * Hook to get consistent label colors across components
 * This ensures that the same label always gets the same color
 */
export function useLabelColors() {
  const { data: labelsData } = useLabels()

  const getLabelColor = useCallback(
    (labelText: string) => {
      if (!labelsData) return 'blank'

      // Find the index of this label in the labels data
      const labelIndex = labelsData.findIndex(
        (item) => item.label === labelText
      )

      if (labelIndex === -1) {
        // If label not found in the labels data, fallback to hash-based color assignment
        // This ensures consistent color for any label even if it's not in the current filter results
        const hash = labelText.split('').reduce((acc, char) => {
          return char.charCodeAt(0) + ((acc << 5) - acc)
        }, 0)
        const index = Math.abs(hash) % Object.keys(labelVariants).length
        const array = Object.keys(labelVariants) as Array<string>
        return getFromIndex(array, index, 0)
      }

      // Use the same color that was assigned in the labels data
      return labelsData[labelIndex].color
    },
    [labelsData]
  )

  return { getLabelColor }
}
