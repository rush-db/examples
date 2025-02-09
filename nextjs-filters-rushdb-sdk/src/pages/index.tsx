'use client'

import { QueryClient, dehydrate } from '@tanstack/react-query'
import Catalog from '@/components/catalog'
import LeftSidebar from '@/components/left-sidebar'
import DebugDrawer from '@/components/debug-drawer'
import { Header } from '@/components/header'
import { Layout } from '@/components/layout'

function Home() {
  return (
    <Layout>
      <div className="flex flex-col min-h-screen">
        <Header />
        <main className="flex flex-1">
          <LeftSidebar />
          <Catalog />
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
