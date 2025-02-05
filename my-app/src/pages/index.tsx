'use client'

import { QueryClient, dehydrate } from '@tanstack/react-query'
import { useState } from 'react'
import Catalog from '@/components/catalog'
import LeftSidebar from '@/components/left-sidebar'
import DebugDrawer from '@/components/debug-drawer'
import { Header } from '@/components/header'
import { Layout } from '@/components/layout'

function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <Layout>
      <div className="flex flex-col min-h-screen">
        <Header onOpenModal={() => setIsModalOpen(true)} />
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

  // await queryClient.prefetchQuery({
  //   queryKey: ['posts', 10],
  //   queryFn: () => fetchPosts(10),
  // })
  //
  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    },
  }
}

export default Home
