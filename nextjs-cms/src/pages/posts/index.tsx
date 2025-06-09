'use client'

import React from 'react'
import { PostsList } from '@/components/posts-list'
import { SidebarLayout } from '@/components/sidebar-layout'

export default function PostsPage() {
  return (
    <SidebarLayout
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Posts' }]}
    >
      <PostsList />
    </SidebarLayout>
  )
}
