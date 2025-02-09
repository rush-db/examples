import { EventEmitter } from 'events'

const logEmitter = new EventEmitter()

let logs: any[] = []

export function pushLog(log: any) {
  if (log && Object.keys(log).length > 0) {
    logs.push(log)
    logEmitter.emit('log', log)
  }
}

export function getLogs() {
  return logs
}

export function subscribeLogs(callback: (log: any) => void) {
  logEmitter.on('log', callback)
  return () => logEmitter.off('log', callback)
}
