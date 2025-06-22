'use client'

import { QueryClient, dehydrate } from '@tanstack/react-query'
import RecordsGrid from '@/components/records-grid'
import { Layout } from '@/components/layout'
import { ControlPanel } from '@/components/control-panel'
import { SidebarLayout } from '@/components/sidebar-layout'
import { SearchProvider } from '@/context/search-context'
import { SearchField } from '@/components/search-field'
import { useSearchContext } from '@/context/search-context'

// Component to conditionally render the search bar
function SearchBarContainer() {
  const { isSearchEnabled } = useSearchContext()

  if (!isSearchEnabled) {
    return null
  }

  return (
    <div className="flex items-center p-4 border-b border-border bg-background/80 backdrop-blur-sm">
      <SearchField />
    </div>
  )
}

interface HomeProps {
  hasBackendUrl?: boolean
  dehydratedState?: any
}

function Home({ hasBackendUrl = false }: HomeProps) {
  return (
    <Layout>
      <SearchProvider initialEnabled={hasBackendUrl}>
        <SidebarLayout>
          <div className="flex flex-col flex-1 overflow-hidden">
            <SearchBarContainer />
            <div className="flex flex-1 overflow-hidden">
              <RecordsGrid />
            </div>
          </div>
        </SidebarLayout>
        <ControlPanel />
      </SearchProvider>
    </Layout>
  )
}

export async function getStaticProps() {
  const queryClient = new QueryClient()

  // Pass backend URL to client if it exists
  const hasBackendUrl =
    typeof process.env.NEXT_PUBLIC_BACKEND_URL === 'string' &&
    process.env.NEXT_PUBLIC_BACKEND_URL.length > 0

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      hasBackendUrl: hasBackendUrl,
    },
  }
}

export default Home
