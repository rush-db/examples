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

export const db = new RushDB(
  'feb27a87391a6325c67c1395583ca7b7eWvkm3GiAaEw8P05gc2/pMexcqubcOuRWQ3uM1aiwKSC8v5dI1LCapZhDnNZtEc2',
  {
    logger: (payload) => {
      prettyLog(payload)
      pushLog(payload)
    },
    options: {
      allowForceDelete: true,
    },
  }
)
