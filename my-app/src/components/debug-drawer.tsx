'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Code } from 'lucide-react'

export default function DebugDrawer() {
  const [isOpen, setIsOpen] = useState(false)

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
        <ScrollArea className="h-full p-4">
          <h2 className="text-lg font-semibold mb-4">Debug Information</h2>
          <pre className="text-sm whitespace-pre-wrap">
            {JSON.stringify(
              {
                timestamp: 123,
              },
              null,
              2
            )}
          </pre>
        </ScrollArea>
      </div>
    </>
  )
}
