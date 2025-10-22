'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { FiltersSidebar } from '@/components/filters-sidebar'
import { Cart } from '@/components/cart'
import {
  ArrowLeft,
  ExternalLink,
  FileText,
  Github,
  Globe,
  Info,
  Bug,
} from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover'
import { Button } from './ui/button'
import { ThemeToggle } from './theme-toggle'
import { Logo } from './logo'
import { cn } from '@/lib/utils'
import { useSearchQuery } from '@/context/search-query-context'

export interface LayoutProps {
  children: React.ReactNode
  title?: string
  initialProperties?: any[]
  showFilters?: boolean
  showCart?: boolean
}

export const Layout = ({
  children,
  title = 'Records',
  initialProperties,
  showFilters = false,
  showCart = true,
}: LayoutProps) => {
  const router = useRouter()
  const isHome = router.pathname === '/'
  const {
    labels = [],
    where = {},
    skip = 0,
    limit = 0,
    orderBy,
  } = useSearchQuery()
  const debugJson = React.useMemo(
    () => JSON.stringify({ labels, where, skip, limit, orderBy }, null, 2),
    [labels, where, skip, limit, orderBy]
  )

  function handleBackClick(e: React.MouseEvent) {
    e.preventDefault()
    if (typeof window !== 'undefined' && window.history.length > 1) {
      router.back()
    } else {
      router.push('/')
    }
  }

  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <div className="flex h-screen">
        <div className={`flex flex-col flex-1 min-w-0`}>
          <header className="flex h-16 shrink-0 justify-between items-center gap-2 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-2">
            <div className="flex items-center gap-2 p-4">
              <Logo />
              {!isHome && (
                <Button
                  type="button"
                  onClick={handleBackClick}
                  variant="ghost"
                  size="icon"
                >
                  <ArrowLeft className="w-4 h-4 inline-block mr-1" />
                </Button>
              )}

              <div>
                <h1 className="text-xl font-semibold text-foreground">
                  {title}
                </h1>
                <p className="text-xs text-muted-foreground mt-1">Demo shop</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link href="/orders">
                <Button variant="outline" size="sm" aria-label="My Orders">
                  <FileText className="w-4 h-4 mr-2" />
                  Orders
                </Button>
              </Link>
              {/* Debug popover: shows current useSearchQuery state */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Debug search state"
                    title="Debug search state"
                  >
                    <Bug className="w-4 h-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-[520px]">
                  <div className="flex flex-col gap-2">
                    <div className="text-xs text-muted-foreground">
                      Current search query
                    </div>
                    <pre className="text-xs bg-muted rounded p-2 overflow-auto max-h-80">
                      <code>{debugJson}</code>
                    </pre>
                  </div>
                </PopoverContent>
              </Popover>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Info and links"
                  >
                    <Info className="w-4 h-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-64">
                  <div className="flex flex-col gap-2">
                    <a
                      href="https://rushdb.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-foreground hover:underline"
                    >
                      <Globe className="w-3 h-3" />
                      <span>RushDB Website</span>
                      <ExternalLink className="w-2.5 h-2.5 ml-auto" />
                    </a>
                    <a
                      href="https://docs.rushdb.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-foreground hover:underline"
                    >
                      <FileText className="w-3 h-3" />
                      <span>Official Documentation</span>
                      <ExternalLink className="w-2.5 h-2.5 ml-auto" />
                    </a>
                    <a
                      href="https://github.com/rush-db/examples/tree/main/nextjs-ecommerce-example"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-foreground hover:underline"
                    >
                      <Github className="w-3 h-3" />
                      <span>View Source Code</span>
                      <ExternalLink className="w-2.5 h-2.5 ml-auto" />
                    </a>
                  </div>
                </PopoverContent>
              </Popover>

              <ThemeToggle />
            </div>
          </header>
          <div className="flex flex-1 overflow-hidden custom-scrollbar">
            {showFilters ? (
              <FiltersSidebar initialProperties={initialProperties} />
            ) : null}
            <div
              className={cn(
                'flex-1 min-w-0 overflow-auto custom-scrollbar p-4',
                {
                  'pl-[256px]': showFilters,
                }
              )}
            >
              {children}
            </div>
            {showCart ? (
              <div className="w-full max-w-72 border-l border-border/50 p-4">
                <Cart />
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </NextThemesProvider>
  )
}
