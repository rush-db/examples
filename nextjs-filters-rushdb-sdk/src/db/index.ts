import RushDB from '@rushdb/javascript-sdk'

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
  'd8540447a152739eea25f4c642208d3cS54i7mw0VIZ++cSQUBZkXXfeXSVV7g6XASqYyrp5dGtxYUrBpHCO7wfEHJ8akf5v',
  {
    logger: (payload) => prettyLog(payload),
    url: 'http://localhost:3000',
  }
)
