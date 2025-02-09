'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Code } from 'lucide-react'
import { JsonViewer } from '@/components/ui/json-viewer'
import { getLogs, subscribeLogs } from '@/lib/log-store'

export default function DebugDrawer() {
  const [isOpen, setIsOpen] = useState(false)
  const [logs, setLogs] = useState<any[]>(getLogs())

  useEffect(() => {
    const unsubscribe = subscribeLogs((newLog) => {
      setLogs((prev) => [...prev, newLog])
    })

    return () => {
      unsubscribe()
    }
  }, [])

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        className="fixed bottom-4 right-4 z-50 rounded-full"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Code className="h-4 w-4" />
        <span className="sr-only">Toggle Debug Info</span>
      </Button>
      <div
        className={`fixed bottom-16 right-4 h-[calc(100vh-5rem)] w-80 bg-background border rounded-lg shadow-lg transform transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <ScrollArea className="h-full p-4 flex flex-col scrollable-content">
          <h2 className="text-lg font-semibold mb-4">Debug Information</h2>

          {logs?.reverse().map((log, index) => {
            return (
              <div key={index} className={'mb-4'}>
                <h3 className="font-semibold mb-2">
                  {log.responseData ? 'Response Data' : 'Request Data'}
                </h3>
                <div className="overflow-x-auto">
                  <JsonViewer data={log} />
                </div>
                {log.responseData ? <hr /> : null}
              </div>
            )
          })}
        </ScrollArea>
      </div>
    </>
  )
}
