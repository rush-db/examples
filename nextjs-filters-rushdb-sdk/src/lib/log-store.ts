import { EventEmitter } from 'events'

const logEmitter = new EventEmitter()

let logs: Record<string, any> = {}

export function pushLog(log: any) {
  if (log && Object.keys(log).length > 0) {
    if (!log.responseData) {
      logs[log.requestId] = {
        ...(logs[log.requestId] || {}),
        ...log,
      }
    } else {
      logs[log.requestId] = {
        ...(logs[log.requestId] || {}),
        ...log,
        responseTime: Date.now(),
      }
    }

    logEmitter.emit('log', logs[log.requestId])
  }
}

export function getLogs() {
  return logs
}

export function subscribeLogs(callback: (log: any) => void) {
  logEmitter.on('log', callback)
  return () => logEmitter.off('log', callback)
}
