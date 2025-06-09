'use client'

import { QueryClient, dehydrate } from '@tanstack/react-query'
import RecordsGrid from '@/components/records-grid'
import { Layout } from '@/components/layout'
import { ControlPanel } from '@/components/control-panel'
import { SidebarLayout } from '@/components/sidebar-layout'

function Home() {
  return (
    <Layout>
      <SidebarLayout>
        <div className="flex flex-1 overflow-hidden">
          <RecordsGrid />
        </div>
      </SidebarLayout>
      <ControlPanel />
    </Layout>
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
