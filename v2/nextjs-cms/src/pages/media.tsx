'use client'

import React from 'react'
import { SidebarLayout } from '@/components/sidebar-layout'

import { MediaManager } from '@/components/media-manager'

export default function MediaRoute() {
  return (
    <SidebarLayout
      breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Media' }]}
    >
      <MediaManager />
    </SidebarLayout>
  )
}
