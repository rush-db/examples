import React from 'react'
import { FiltersSidebar } from '@/components/filters-sidebar'
import DebugSidebar from '@/components/debug-drawer'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Code2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getLogs, subscribeLogs } from '@/lib/log-store'
import {
  SidebarProvider as CustomSidebarProvider,
  useSidebar as useCustomSidebar,
} from '@/context/sidebar-context'
import { useRecords } from '@/hooks/use-records'
import { WelcomeModal } from './welcome-modal'
import { ApiTokenModal } from './api-token-modal'

interface SidebarLayoutProps {
  children: React.ReactNode
  title?: string
}

export function SidebarLayout({
  children,
  title = 'Records',
}: SidebarLayoutProps) {
  return (
    <CustomSidebarProvider>
      <SidebarLayoutContent title={title}>{children}</SidebarLayoutContent>
    </CustomSidebarProvider>
  )
}

function SidebarLayoutContent({ children, title }: SidebarLayoutProps) {
  const { toggleRightSidebar } = useCustomSidebar()
  const [logCount, setLogCount] = useState(0)
  const { data: records, isLoading, isFetching } = useRecords()

  useEffect(() => {
    const logs = getLogs()
    setLogCount(Object.keys(logs).length)

    const unsubscribe = subscribeLogs(() => {
      const updatedLogs = getLogs()
      setLogCount(Object.keys(updatedLogs).length)
    })

    return () => {
      unsubscribe()
    }
  }, [])

  return (
    <div className="flex h-screen">
      {/* Static Filters Sidebar - Always visible */}
      <FiltersSidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 pl-80">
        <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-2">
          <div className="flex items-center gap-2 p-4">
            <div>
              <h1 className="text-xl font-semibold text-foreground">Records</h1>
              <p className="text-xs text-muted-foreground mt-1">
                Explore {records?.total || 0} records in your database
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 ml-auto px-4">
            <ApiTokenModal />
            <WelcomeModal />
            <div className="h-6 w-px bg-border"></div>
            <Button
              variant="outline"
              size="icon"
              onClick={toggleRightSidebar}
              className="relative"
            >
              <Code2 className="h-4 w-4" />
              <span className="sr-only">Toggle debug console</span>
              {logCount > 0 && (
                <Badge
                  variant="destructive"
                  className="absolute -top-2 -right-2 h-6 w-6 p-0 flex items-center justify-center text-[10px] font-medium"
                >
                  {logCount > 99 ? '99+' : logCount}
                </Badge>
              )}
            </Button>
          </div>
        </header>
        <div className="flex flex-1 custom-scrollbar">{children}</div>
      </div>

      <DebugSidebar />
    </div>
  )
}
