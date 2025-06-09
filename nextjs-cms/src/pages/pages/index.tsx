'use client'

import React from 'react'
import { PagesList } from '@/components/pages-list'
import { SidebarLayout } from '@/components/sidebar-layout'

export default function PagesPage() {
  return (
    <SidebarLayout
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Pages' }]}
    >
      <PagesList />
    </SidebarLayout>
  )
}
