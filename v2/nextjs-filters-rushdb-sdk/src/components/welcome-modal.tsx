'use client'

import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { JsonViewer } from '@/components/ui/json-viewer'
import testDataset from '@/dataset/test-data-example.json'
import { Database } from 'lucide-react'

export function WelcomeModal() {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const hideWelcome = localStorage.getItem('hideWelcomeModal')

    if (!hideWelcome) {
      setIsOpen(true)
    }
  }, [])

  function handleClose() {
    setIsOpen(false)
    localStorage.setItem('hideWelcomeModal', 'true')
  }

  function onChangeOpen(value: boolean) {
    setIsOpen(value)

    if (!value) {
      localStorage.setItem('hideWelcomeModal', 'true')
    }
  }

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onChangeOpen}>
        <DialogContent className="w-full max-w-full sm:w-[90%] sm:h-[90%]">
          <DialogHeader>
            <DialogTitle>Welcome to the Rushdb Demo App</DialogTitle>
            <DialogDescription>
              This dataset is provided to demonstrate dynamic filters, search
              functionality, and pagination in RushDB. The complete source
              dataset is shown below:
            </DialogDescription>
          </DialogHeader>
          <div className="overflow-y-auto">
            <JsonViewer data={testDataset} collapsedRow={3} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleClose}>
              Confirm &amp; Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Button variant="outline" onClick={() => setIsOpen(true)}>
        Example Dataset <Database className="w-4 h-4" />
      </Button>
    </>
  )
}
