'use client'

import { useState } from 'react'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import RecordsGrid from '@/components/records-grid'
import { Layout } from '@/components/layout'
import { SearchProvider } from '@/context/search-context'
import { SearchField } from '@/components/search-field'
import { useSearchContext } from '@/context/search-context'
import { Search, Settings, Database, Play, ChevronDown } from 'lucide-react'
import { SidebarLayout } from '@/components/sidebar-layout'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

// Settings component for vector dimension
function SearchSettings() {
  const { searchSettings, updateSearchSettings } = useSearchContext()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Settings className="w-4 h-4" />
          Settings
          <ChevronDown className="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-80 p-4">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="vector-dimension">Vector Dimension</Label>
            <Select
              value={searchSettings.vectorDimension.toString()}
              onValueChange={(value) =>
                updateSearchSettings({ vectorDimension: Number(value) })
              }
            >
              <SelectTrigger id="vector-dimension">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="384">
                  384 (sentence-transformers/all-MiniLM-L6-v2)
                </SelectItem>
                <SelectItem value="768">
                  768 (sentence-transformers/all-mpnet-base-v2)
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground">
              This setting affects the search and indexing operations
            </p>
          </div>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// Index Control Panel component
function IndexControlPanel() {
  const [isIndexing, setIsIndexing] = useState(false)
  const [lastOperation, setLastOperation] = useState<string | null>(null)
  const { searchSettings } = useSearchContext()

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL
  const isEnabled = typeof backendUrl === 'string' && backendUrl.length > 0

  const handleRunIndexing = async () => {
    if (!isEnabled) return

    setIsIndexing(true)
    setLastOperation(null)

    try {
      const response = await fetch(`${backendUrl}/index`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          labels: ['BOOK'],
          field: 'description',
          vector_dimension: searchSettings.vectorDimension,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to start indexing')
      }

      const result = await response.json()
      setLastOperation(
        `Indexing completed: ${result.processed_count} processed, ${result.error_count} errors`
      )
    } catch (error) {
      setLastOperation(
        `Indexing failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    } finally {
      setIsIndexing(false)
    }
  }

  if (!isEnabled) {
    return (
      <Card className="mx-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Index Control Panel
          </CardTitle>
          <CardDescription>
            Backend URL not configured. Please set NEXT_PUBLIC_BACKEND_URL
            environment variable.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="mx-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="w-5 h-5" />
          Index Control Panel
        </CardTitle>
        <CardDescription>
          Manage the vector index for your RAG system
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Query Display */}
        <div className="space-y-2">
          <Label>Current Index Configuration</Label>
          <div className="bg-muted p-3 rounded-md text-sm font-mono">
            <div>
              labels: <Badge variant="secondary">["BOOK"]</Badge>
            </div>
            <div>
              field: <Badge variant="secondary">"description"</Badge>
            </div>
            <div>
              vector_dimension:{' '}
              <Badge variant="secondary">
                {searchSettings.vectorDimension}
              </Badge>
            </div>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleRunIndexing}
            disabled={isIndexing}
            className="flex-1"
          >
            {isIndexing ? (
              <>
                <Database className="w-4 h-4 mr-2 animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Indexing
              </>
            )}
          </Button>
        </div>

        {/* Operation Result */}
        {lastOperation && (
          <div className="space-y-2">
            <Label>Last Operation Result</Label>
            <div className="bg-muted p-3 rounded-md text-sm">
              {lastOperation}
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="text-xs text-muted-foreground pt-2 border-t">
          <p>
            <strong>Run Indexing:</strong> Creates vector embeddings for all
            records with BOOK labels and adds them directly to the records
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

// Enhanced search interface with settings
function EnhancedSearchField() {
  return (
    <div className="flex items-center gap-2 w-full max-w-2xl">
      <div className="flex-1">
        <SearchField />
      </div>
      <SearchSettings />
    </div>
  )
}

// Component to render the centered search interface
function CenteredSearchContainer() {
  const { isSearchEnabled, searchText } = useSearchContext()

  if (!isSearchEnabled) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[30vh] px-4">
        <div className="text-center space-y-4">
          <Search className="w-16 h-16 text-muted-foreground mx-auto" />
          <h2 className="text-2xl font-semibold text-foreground">
            Search Not Available
          </h2>
          <p className="text-muted-foreground max-w-md">
            Backend URL is not configured. Please set NEXT_PUBLIC_BACKEND_URL
            environment variable.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[30vh] px-4">
      <div className="w-full max-w-4xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <Search className="w-12 h-12 text-primary mx-auto" />
          <h1 className="text-3xl font-bold text-foreground">RAG Search</h1>
          <p className="text-muted-foreground">
            Search through your records with intelligent results
          </p>
        </div>

        {/* Enhanced Search Field with Settings */}
        <div className="flex justify-center">
          <EnhancedSearchField />
        </div>

        {/* Search hint */}
        {!searchText && (
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              Start typing to search through your records...
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

interface RagSearchProps {
  hasBackendUrl?: boolean
  dehydratedState?: any
}

function RagSearch({ hasBackendUrl = false }: RagSearchProps) {
  return (
    <Layout>
      <SearchProvider initialEnabled={hasBackendUrl}>
        <div className="min-h-screen bg-background">
          {/* Main container */}
          <div className="flex flex-col">
            {/* Centered search section */}
            <CenteredSearchContainer />

            {/* Index Control Panel */}
            <div className="py-6">
              <IndexControlPanel />
            </div>

            {/* Results section */}
            <div className="flex-1 px-4 pb-8">
              <div className="max-w-7xl mx-auto">
                <RecordsGrid />
              </div>
            </div>
          </div>
        </div>
      </SearchProvider>
    </Layout>
  )
}

export default RagSearch
