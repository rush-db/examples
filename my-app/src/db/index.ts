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
  '45f93e7acc299734e1b72904d90a9e00gGblPzS0FsUNzVpt2xBT6GbKpDFDy6se9bUbsGWPVoL6lkZm5aSsuH3CxkYM7Om5',
  {
    logger: (payload) => prettyLog(payload),
    url: 'https://api.rushdb.com',
  }
)
