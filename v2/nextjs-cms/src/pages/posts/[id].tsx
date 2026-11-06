'use client'

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/router'
import { PostForm } from '@/components/post-form'

import { PostModel } from '@/models'

export default function EditPostPage() {
  const router = useRouter()
  const { id } = router.query

  // Fetch the post data
  const {
    data: post,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['post', id],
    queryFn: async () => {
      if (!id || typeof id !== 'string') return null

      const result = await PostModel.findById(id)
      if (!result.exists()) {
        throw new Error('Post not found')
      }

      return result
    },
    enabled: !!id,
  })

  return (
    <PostForm
      isEdit={true}
      initialData={post || undefined}
      isLoading={isLoading}
    />
  )
}
