'use client'

// filepath: /Users/onepx/personal/examples/nextjs-filters-rushdb-sdk/src/db/index.ts
import RushDB from '@rushdb/javascript-sdk'
import { pushLog } from '@/lib/log-store'

const styles = {
  key: 'color: #2196F3; font-weight: bold',
  string: 'color: #4CAF50',
  number: 'color: #FF9800',
  boolean: 'color: #673AB7',
  null: 'color: #F44336',
}

function prettyLog(obj: any) {
  console.group('RushDB API Request Details:')
  Object.entries(obj).forEach(([key, value]) => {
    const valueStyle =
      typeof value === 'string'
        ? styles.string
        : typeof value === 'number'
          ? styles.number
          : typeof value === 'boolean'
            ? styles.boolean
            : value === null
              ? styles.null
              : ''

    console.log('%c%s%c %o', styles.key, key + ':', valueStyle, value)
  })
  console.groupEnd()
}

const DEFAULT_API_TOKEN =
  '45f93e7acc299734e1b72904d90a9e00gGblPzS0FsUNzVpt2xBT6GbKpDFDy6se9bUbsGWPVoL6lkZm5aSsuH3CxkYM7Om5'
const API_KEY_STORAGE_KEY = 'rushdb-api-key'

// Get the API token from localStorage or use the default
const getApiToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(API_KEY_STORAGE_KEY) || DEFAULT_API_TOKEN
  }
  return DEFAULT_API_TOKEN
}

export const db = new RushDB(getApiToken(), {
  logger: (payload) => {
    prettyLog(payload)
    pushLog(payload)
  },
  options: {
    allowForceDelete: true,
  },
})
