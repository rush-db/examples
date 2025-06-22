'use client'

import React, { createContext, useContext, useState } from 'react'

interface SidebarContextType {
  rightSidebarOpen: boolean
  toggleRightSidebar: () => void
  setRightSidebar: (open: boolean) => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false)

  const toggleRightSidebar = () => setRightSidebarOpen(!rightSidebarOpen)
  const setRightSidebar = (open: boolean) => setRightSidebarOpen(open)

  return (
    <SidebarContext.Provider
      value={{
        rightSidebarOpen,
        toggleRightSidebar,
        setRightSidebar,
      }}
    >
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  const context = useContext(SidebarContext)
  // if (context === undefined) {
  //   throw new Error('useSidebar must be used within a SidebarProvider')
  // }
  return context
}
