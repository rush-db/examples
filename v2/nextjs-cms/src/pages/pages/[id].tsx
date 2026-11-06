import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/router'
import { PageForm } from '@/components/page-form'

import { PageModel } from '@/models'

export default function EditPagePage() {
  const router = useRouter()
  const { id } = router.query

  // Fetch the page data
  const { data: page, isLoading } = useQuery({
    queryKey: ['page', id],
    queryFn: async () => {
      if (!id || typeof id !== 'string') return null

      const result = await PageModel.findById(id)
      if (!result.exists()) {
        throw new Error('Page not found')
      }

      return result
    },
    enabled: !!id,
  })

  return (
    <PageForm
      isEdit={true}
      initialData={page || undefined}
      isLoading={isLoading}
    />
  )
}
