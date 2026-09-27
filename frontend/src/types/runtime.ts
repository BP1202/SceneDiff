export type RuntimeStatus = 'idle' | 'queued' | 'launching_browser' | 'navigating' | 'collecting_dom' | 'collecting_network' | 'collecting_storage' | 'completed' | 'failed'

export interface RuntimeTraceLog {
  id: string
  timestamp: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  phase?: string
}

export interface RuntimeExecution {
  id: string
  commitSha: string
  status: RuntimeStatus
  durationMs: number
  domNodesCaptured: number
  networkRequestsCaptured: number
  consoleMessagesCaptured: number
  storageKeysCaptured: number
  screenshotUrl?: string
  logs: RuntimeTraceLog[]
}
