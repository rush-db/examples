'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Code, Loader } from 'lucide-react'
import { JsonViewer } from '@/components/ui/json-viewer'
import { getLogs, subscribeLogs } from '@/lib/log-store'

export default function DebugDrawer() {
  const [isOpen, setIsOpen] = useState(false)
  const [logs, setLogs] = useState(getLogs())

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

  return (
    <>
      <Button
        variant="default"
        size="icon"
        className="fixed bottom-4 right-4 z-[999] rounded-full"
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setIsOpen(!isOpen)
        }}
      >
        <Code className="h-4 w-4" />
        <span className="sr-only">Toggle Debug Info</span>
      </Button>
      <div
        className={`fixed bottom-16 right-4 h-[calc(100vh-5rem)] w-96 bg-background border rounded-lg shadow-lg transform transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <ScrollArea className="h-full p-4 flex flex-col scrollable-content">
          <h2 className="text-lg font-semibold mb-4">API Calls</h2>

          {Object.values(logs)
            ?.reverse()
            .map(({ requestId, method, path, headers, ...log }) => {
              const dataToDisplay = Object.keys(headers).length
                ? { ...log, headers }
                : log
              return (
                <div key={requestId} className={'mb-4 border-t'}>
                  <div className="font-semibold py-2 pt-3 flex items-center justify-between w-full">
                    <pre>
                      {method}
                      <span className="text-blue-500 text-wrap">
                        {decodeURI(path)}
                      </span>
                    </pre>
                    {!log.responseData ? (
                      <Loader className="animate-spin inline" />
                    ) : null}
                  </div>
                  <p className="text-xs text-gray-500 mb-4">{requestId}</p>
                  <div className="overflow-x-auto">
                    <JsonViewer data={dataToDisplay} />
                  </div>
                </div>
              )
            })}
        </ScrollArea>
      </div>
    </>
  )
}
