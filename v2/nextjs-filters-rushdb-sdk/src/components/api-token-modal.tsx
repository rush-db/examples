'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'

const API_KEY_STORAGE_KEY = 'rushdb-api-key'

export function ApiTokenModal() {
  const [open, setOpen] = useState(false)
  const [apiToken, setApiToken] = useState('')
  const [hasCustomToken, setHasCustomToken] = useState(false)

  useEffect(() => {
    // Check if a custom token exists in localStorage
    const storedToken = localStorage.getItem(API_KEY_STORAGE_KEY)
    setHasCustomToken(!!storedToken)
    if (storedToken) {
      // Mask the token for display
      setApiToken(
        '•'.repeat(20) + storedToken.substring(storedToken.length - 10)
      )
    }
  }, [open])

  const saveToken = () => {
    if (apiToken && apiToken.trim() !== '') {
      localStorage.setItem(API_KEY_STORAGE_KEY, apiToken.trim())
      toast({
        title: 'API Token Updated',
        description:
          'Your custom RushDB API token has been saved. Reload the page to apply changes.',
      })
      setHasCustomToken(true)
      setOpen(false)
      window.location.reload() // Reload to apply the new token
    } else {
      toast({
        title: 'Invalid API Token',
        description: 'Please enter a valid API token.',
        variant: 'destructive',
      })
    }
  }

  const resetToken = () => {
    localStorage.removeItem(API_KEY_STORAGE_KEY)
    toast({
      title: 'API Token Reset',
      description:
        'Now using the default RushDB API token. Reload the page to apply changes.',
    })
    setHasCustomToken(false)
    setApiToken('')
    setOpen(false)
    window.location.reload() // Reload to apply the default token
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          {hasCustomToken ? 'Custom API Token' : 'Set API Token'}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>RushDB API Token</DialogTitle>
          <DialogDescription>
            {hasCustomToken
              ? 'You are using a custom API token. You can update or reset it.'
              : 'Enter a custom RushDB API token to use instead of the default one.'}
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center space-y-2 py-4">
          <div className="grid flex-1 gap-2">
            <Label htmlFor="api-token" className="sr-only">
              API Token
            </Label>
            <Input
              id="api-token"
              placeholder="Enter your RushDB API token"
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
              className="w-full"
            />
          </div>
        </div>
        <DialogFooter className="flex justify-between sm:justify-between">
          {hasCustomToken && (
            <Button variant="destructive" onClick={resetToken}>
              Reset to Default
            </Button>
          )}
          <div className="flex space-x-2">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveToken}>Save</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
