'use client'

import { QueryClient, dehydrate } from '@tanstack/react-query'
import { CMSDashboard } from '@/components/cms-dashboard'
import { SidebarLayout } from '@/components/sidebar-layout'

function Home() {
  return (
    <SidebarLayout title="Dashboard">
      <CMSDashboard />
    </SidebarLayout>
  )
}

export async function getStaticProps() {
  const queryClient = new QueryClient()

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    },
  }
}

export default Home
