import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertCircle, Database, Play, Copy, CheckCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

import { PostModel, PageModel } from '@/models'

interface QueryExample {
  name: string
  description: string
  model: string
  query: object
  explanation: string
}

const queryExamples: QueryExample[] = [
  {
    name: 'Find All Posts',
    description: 'Basic query to fetch all posts',
    model: 'PostModel',
    query: { limit: 10 },
    explanation: 'Simple query with limit - showcases basic RushDB syntax',
  },
  {
    name: 'Published Posts Only',
    description: 'Filter posts by draft status',
    model: 'PostModel',
    query: {
      where: { draft: false },
      orderBy: { createdAt: 'desc' },
      limit: 5,
    },
    explanation:
      'Boolean filtering with ordering - demonstrates type-safe where clauses',
  },
  {
    name: 'Featured Content',
    description: 'Find featured posts and blog posts',
    model: 'PostModel',
    query: {
      where: { featured: true },
      orderBy: { publishedAt: 'desc' },
      aggregate: {
        title: '$record.title',
        author: '$record.author',
        publishedAt: '$record.publishedAt',
      },
    },
    explanation:
      'Field selection with filtering - showcases selective data fetching',
  },
  {
    name: 'Search by Author',
    description: 'Find content by specific author',
    model: 'PostModel',
    query: {
      where: { author: 'Sarah Johnson' },
      limit: 10,
    },
    explanation: 'String matching - demonstrates exact value filtering',
  },
  {
    name: 'Recent Content',
    description: 'Get content from the last 30 days',
    model: 'PostModel',
    query: {
      where: {
        createdAt: {
          $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        },
      },
      orderBy: { createdAt: 'desc' },
    },
    explanation: 'Date range filtering - shows advanced where clause operators',
  },
  {
    name: 'Tag Search',
    description: 'Find posts with specific tags',
    model: 'PostModel',
    query: {
      where: {
        tags: { $in: ['typescript', 'database'] },
      },
      limit: 10,
    },
    explanation:
      'Array field filtering - demonstrates $in operator for multiple values',
  },
]

export function APIExplorer() {
  const [selectedExample, setSelectedExample] = useState<QueryExample>(
    queryExamples[0]
  )
  const [customQuery, setCustomQuery] = useState('')
  const [selectedModel, setSelectedModel] = useState('PostModel')
  const [activeTab, setActiveTab] = useState('examples')
  const [copied, setCopied] = useState(false)

  // Execute the selected query
  const {
    data: queryResult,
    isLoading,
    isRefetching,
    isFetching,
    isPending,

    error,
    refetch,
  } = useQuery({
    queryKey: [
      'api-explorer',
      selectedExample,
      customQuery,
      selectedModel,
      activeTab,
    ],
    queryFn: async () => {
      try {
        let model
        let query

        if (activeTab === 'examples') {
          // Use predefined example
          switch (selectedExample.model) {
            case 'PostModel':
              model = PostModel
              break
            case 'PageModel':
              model = PageModel
              break
            default:
              model = PostModel
          }
          query = selectedExample.query
        } else {
          // Use custom query
          if (!customQuery.trim()) return null

          switch (selectedModel) {
            case 'PostModel':
              model = PostModel
              break
            case 'PageModel':
              model = PageModel
              break
            default:
              model = PostModel
          }

          query = JSON.parse(customQuery)
        }

        const result = await (model as any).find(query)
        return {
          success: true,
          data: result.data,
          count: result.data?.length || 0,
          query,
          model:
            activeTab === 'examples' ? selectedExample.model : selectedModel,
        }
      } catch (error: any) {
        return {
          success: false,
          error: error?.message || 'Unknown error occurred',
          query: activeTab === 'examples' ? selectedExample.query : customQuery,
        }
      }
    },
    enabled: false, // Disable automatic execution, use manual refetch only
  })

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const formatQuery = (query: object) => {
    return JSON.stringify(query, null, 2)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Database className="h-6 w-6" />
          RushDB API Explorer
        </h2>
        <p className="text-muted-foreground mt-1">
          Explore RushDB's powerful querying capabilities with TypeScript safety
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="examples">Query Examples</TabsTrigger>
          <TabsTrigger value="custom">Custom Query</TabsTrigger>
        </TabsList>

        <TabsContent value="examples" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Query Examples List */}
            <Card>
              <CardHeader>
                <CardTitle>Example Queries</CardTitle>
                <CardDescription>
                  Explore different RushDB query patterns and capabilities
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {queryExamples.map((example, index) => (
                    <div
                      key={index}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedExample === example
                          ? 'border-primary bg-primary/5'
                          : 'hover:bg-muted/50'
                      }`}
                      onClick={() => setSelectedExample(example)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{example.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {example.description}
                          </p>
                          <Badge variant="outline" className="mt-2 text-xs">
                            {example.model}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Query Details and Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  {selectedExample.name}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      copyToClipboard(formatQuery(selectedExample.query))
                    }
                    className="flex items-center gap-2"
                  >
                    {copied ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                    {copied ? 'Copied!' : 'Copy'}
                  </Button>
                </CardTitle>
                <CardDescription>{selectedExample.explanation}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Query Code */}
                <div>
                  <Label className="text-sm font-medium">Query</Label>
                  <pre className="mt-2 p-3 bg-muted rounded-md text-sm overflow-x-auto">
                    <code className="text-muted-foreground">
                      {formatQuery(selectedExample.query)}
                    </code>
                  </pre>
                </div>

                {/* Execute Button */}
                <Button
                  onClick={() => refetch()}
                  disabled={isLoading || isFetching}
                  className="w-full flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  {isFetching ? 'Executing...' : 'Execute Query'}
                </Button>

                {/* Results */}
                {queryResult && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <Badge
                        variant={
                          queryResult.success ? 'default' : 'destructive'
                        }
                      >
                        {queryResult.success
                          ? `${queryResult.count} results`
                          : 'Error'}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        Model: {queryResult.model}
                      </span>
                    </div>

                    {queryResult.success ? (
                      <div className="border rounded-md bg-muted">
                        <pre className="p-3 text-sm overflow-x-auto max-h-96">
                          <code className="text-muted-foreground">
                            {JSON.stringify(queryResult.data, null, 2)}
                          </code>
                        </pre>
                      </div>
                    ) : (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{queryResult.error}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="custom" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Custom Query Input */}
            <Card>
              <CardHeader>
                <CardTitle>Custom Query Builder</CardTitle>
                <CardDescription>
                  Write your own RushDB queries and see the results
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="model-select">Select Model</Label>
                  <Select
                    value={selectedModel}
                    onValueChange={setSelectedModel}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PostModel">PostModel</SelectItem>
                      <SelectItem value="PageModel">PageModel</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="query-input">Query (JSON)</Label>
                  <Textarea
                    id="query-input"
                    placeholder='{"where": {"draft": false}, "limit": 10}'
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    className="font-mono text-sm"
                    rows={8}
                  />
                </div>

                <Button
                  onClick={() => refetch()}
                  disabled={isLoading || !customQuery.trim() || isFetching}
                  className="w-full flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  {isLoading || isFetching ? 'Executing...' : 'Execute Query'}
                </Button>
              </CardContent>
            </Card>

            {/* Custom Query Results */}
            <Card>
              <CardHeader>
                <CardTitle>Query Results</CardTitle>
                <CardDescription>
                  Real-time results from your custom queries
                </CardDescription>
              </CardHeader>
              <CardContent>
                {queryResult ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4">
                      <Badge
                        variant={
                          queryResult.success ? 'default' : 'destructive'
                        }
                      >
                        {queryResult.success
                          ? `${queryResult.count} results`
                          : 'Error'}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        Model: {queryResult.model}
                      </span>
                    </div>

                    {queryResult.success ? (
                      <div className="border rounded-md bg-muted">
                        <pre className="p-3 text-sm overflow-x-auto max-h-96">
                          <code className="text-muted-foreground">
                            {JSON.stringify(queryResult.data, null, 2)}
                          </code>
                        </pre>
                      </div>
                    ) : (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{queryResult.error}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Enter a query and click execute to see results
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* RushDB Features Showcase */}
      <Card>
        <CardHeader>
          <CardTitle>RushDB Features Showcase</CardTitle>
          <CardDescription>
            Key features demonstrated in this CMS application
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">TypeScript Safety</h4>
              <p className="text-sm text-muted-foreground">
                Full type inference and safety across all database operations
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Advanced Filtering</h4>
              <p className="text-sm text-muted-foreground">
                Powerful where clauses with operators like $gt, $in, $regex
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Field Selection</h4>
              <p className="text-sm text-muted-foreground">
                Choose specific fields to optimize performance and bandwidth
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Ordering & Pagination</h4>
              <p className="text-sm text-muted-foreground">
                Built-in sorting and pagination for efficient data handling
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Schema Validation</h4>
              <p className="text-sm text-muted-foreground">
                Automatic validation based on defined schemas and types
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Real-time Updates</h4>
              <p className="text-sm text-muted-foreground">
                Reactive data with automatic cache invalidation
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
