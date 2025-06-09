'use client'

import React from 'react'
import { APIExplorer } from '@/components/api-explorer'
import { SidebarLayout } from '@/components/sidebar-layout'

export default function APIExplorerRoute() {
  return (
    <SidebarLayout
      breadcrumbs={[
        { label: 'Dashboard', href: '/' },
        { label: 'API Explorer' },
      ]}
    >
      <APIExplorer />
    </SidebarLayout>
  )
}
