'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSidebar } from '@/context/sidebar-context'
import {
  Loader,
  Clock,
  Server,
  Terminal,
  CheckCircle,
  ChevronLeft,
  DatabaseIcon,
} from 'lucide-react'
import { JsonViewer } from '@/components/ui/json-viewer'
import { getLogs, subscribeLogs } from '@/lib/log-store'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

// Log detail component
interface LogDetailProps {
  log: any
}

function LogDetail({ log }: LogDetailProps) {
  const {
    requestId,
    method,
    path,
    headers,
    requestTime,
    responseTime,
    responseData,
    requestData,
  } = log
  const duration =
    responseTime && requestTime ? responseTime - requestTime : null

  // Organize data for display
  const dataToDisplay = {
    requestInfo: {
      id: requestId,
      method,
      path: decodeURI(path),
    },
    ...(requestData && { request: requestData }),
    ...(headers && Object.keys(headers).length && { headers }),
    ...(responseData && { response: responseData }),
    ...(duration !== null && { performance: { durationMs: duration } }),
  }

  return (
    <div className="space-y-4">
      <Card className="border border-border shadow-sm bg-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base flex items-center gap-2 min-w-0">
              <DatabaseIcon className="h-4 w-4 text-primary flex-shrink-0" />
              <span className="truncate">Request Details</span>
            </CardTitle>
            <Badge
              variant={!responseData ? 'outline' : 'success'}
              className="flex-shrink-0"
            >
              {responseData ? 'Complete' : 'Pending'}
            </Badge>
          </div>
          <CardDescription className="text-xs font-mono truncate">
            {requestId}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 text-sm mb-3">
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">
                Method
              </div>
              <div className="font-mono text-sm bg-muted rounded px-2 py-1 border border-border">
                {method}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">
                Path
              </div>
              <div className="font-mono text-sm bg-muted rounded px-2 py-1 border border-border">
                <div className="min-w-0 break-all text-xs leading-relaxed">
                  {decodeURI(path)}
                </div>
              </div>
            </div>
            {duration !== null && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-muted-foreground">
                  Duration
                </div>
                <div className="font-mono text-sm bg-muted rounded px-2 py-1 border border-border">
                  {duration}ms
                </div>
              </div>
            )}
          </div>

          <Separator className="my-4" />

          <div className="bg-muted rounded-lg border border-border p-4 overflow-hidden">
            <div className="overflow-x-auto overflow-y-auto max-h-96 custom-scrollbar">
              <div className="min-w-0">
                <JsonViewer data={dataToDisplay} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function DebugSidebar() {
  const { rightSidebarOpen } = useSidebar()
  const [logs, setLogs] = useState(getLogs())
  const [selectedLog, setSelectedLog] = useState<string | null>(null)

  useEffect(() => {
    const unsubscribe = subscribeLogs((newLog) => {
      setLogs((prev) => {
        const updatedLogs = { ...prev, [newLog.requestId]: newLog }
        return Object.fromEntries(Object.entries(updatedLogs).slice(-100))
      })
    })

    return () => {
      unsubscribe()
    }
  }, [])

  if (!rightSidebarOpen) return null

  return (
    <div className="w-80 flex-shrink-0 shadow-sm overflow-hidden">
      <div className="flex h-full bg-muted/20   flex-col min-w-0 fixed border-l border-border/50">
        {/* Header */}
        <div className="bg-background/95 backdrop-blur-sm border-b border-border/50 p-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <Server className="h-5 w-5 text-primary flex-shrink-0" />
              <h2 className="text-lg font-semibold truncate">API Logs</h2>
            </div>
            <Badge
              variant="outline"
              className="flex items-center gap-1 px-2 flex-shrink-0"
            >
              <Clock className="h-3 w-3" />
              <span className="text-xs">{Object.keys(logs).length}</span>
            </Badge>
          </div>
          <CardDescription className="mt-1 text-xs text-muted-foreground">
            Monitor and inspect API requests in real-time
          </CardDescription>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1 overflow-hidden">
          <div className="custom-scrollbar h-full">
            {selectedLog ? (
              <div className="p-4">
                <Button
                  variant="ghost"
                  size="sm"
                  className="mb-4"
                  onClick={() => setSelectedLog(null)}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Back to all requests
                </Button>

                <LogDetail log={logs[selectedLog]} />
              </div>
            ) : (
              <div className="p-4 space-y-4">
                {Object.values(logs)
                  ?.reverse()
                  .map(
                    ({
                      requestId,
                      method,
                      path,
                      responseData,
                      requestTime,
                    }) => {
                      const hasResponse = !!responseData

                      return (
                        <Card
                          key={requestId}
                          className="border border-border shadow-sm bg-card hover:border-foreground/20 transition-all cursor-pointer"
                          onClick={() => setSelectedLog(requestId)}
                        >
                          <CardHeader className="p-3 pb-2">
                            <div className="flex items-center justify-between gap-2">
                              <Badge
                                variant={!hasResponse ? 'outline' : 'success'}
                                className="h-6 flex-shrink-0"
                              >
                                {method}
                              </Badge>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                {!hasResponse ? (
                                  <Loader className="h-3 w-3 animate-spin text-muted-foreground" />
                                ) : (
                                  <CheckCircle className="h-3 w-3 text-green-500" />
                                )}
                                {hasResponse && (
                                  <span className="text-xs font-mono">
                                    Complete
                                  </span>
                                )}
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent className="p-3 pt-0">
                            <div className="font-mono text-xs text-muted-foreground mb-1 break-all">
                              {decodeURI(path)}
                            </div>

                            <div className="flex items-center justify-between text-xs mt-2 gap-2">
                              <span className="text-muted-foreground flex-shrink-0">
                                {new Date(
                                  requestTime || Date.now()
                                ).toLocaleTimeString()}
                              </span>
                              <span className="text-xs text-muted-foreground font-mono opacity-60 flex-shrink-0">
                                #{requestId.slice(-6)}
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      )
                    }
                  )}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t border-border/50 bg-muted/50 p-3 flex-shrink-0">
          <div className="flex items-center justify-center">
            <div className="text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Terminal className="h-3 w-3" />
                Debug Mode Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
