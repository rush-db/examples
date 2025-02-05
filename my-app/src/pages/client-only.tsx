import React, { useState } from 'react'
import LeftSidebar from '@/components/left-sidebar'
import Catalog from '@/components/catalog'
import DebugDrawer from '@/components/debug-drawer'
import { Header } from '@/components/header'

function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <div className="flex flex-col min-h-screen">
      <Header onOpenModal={() => setIsModalOpen(true)} />
      <main className="flex flex-1">
        <LeftSidebar />
        <Catalog />
        <DebugDrawer />
      </main>
    </div>
  )
}

export default Home
