'use client'

import { QueryClient, dehydrate } from '@tanstack/react-query'
import RecordsGrid from '@/components/records-grid'
import LeftSidebar from '@/components/left-sidebar'
import { Layout } from '@/components/layout'
import DebugDrawer from '@/components/debug-drawer'

function Home() {
  return (
    <Layout>
      <div className="flex flex-col min-h-screen">
        <main className="flex flex-1">
          <LeftSidebar />
          <RecordsGrid />
          <DebugDrawer />
        </main>
      </div>
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
