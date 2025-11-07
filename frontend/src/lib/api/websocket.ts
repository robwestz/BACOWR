import { io, Socket } from 'socket.io-client'
import type { WSJobUpdate } from '@/types'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

type EventHandler<T = any> = (data: T) => void

class WebSocketClient {
  private socket: Socket | null = null
  private listeners: Map<string, Set<EventHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(): void {
    if (this.socket?.connected) return

    this.socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      this.emit('connection', { connected: true })
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
      this.emit('connection', { connected: false })
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.reconnectAttempts++

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached')
        this.emit('error', { message: 'Failed to connect to server' })
      }
    })

    // Job-specific events
    this.socket.on('job:update', (data: WSJobUpdate) => {
      this.emit('job:update', data)
      this.emit(`job:${data.job_id}`, data)
    })

    this.socket.on('job:completed', (data: WSJobUpdate) => {
      this.emit('job:completed', data)
      this.emit(`job:${data.job_id}:completed`, data)
    })

    this.socket.on('job:error', (data: WSJobUpdate) => {
      this.emit('job:error', data)
      this.emit(`job:${data.job_id}:error`, data)
    })

    // Batch events
    this.socket.on('batch:update', (data) => {
      this.emit('batch:update', data)
    })
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.listeners.clear()
  }

  // Subscribe to specific job updates
  subscribeToJob(jobId: string): void {
    if (!this.socket) this.connect()
    this.socket?.emit('subscribe:job', { job_id: jobId })
  }

  // Unsubscribe from job updates
  unsubscribeFromJob(jobId: string): void {
    this.socket?.emit('unsubscribe:job', { job_id: jobId })
  }

  // Subscribe to batch updates
  subscribeToBatch(batchId: string): void {
    if (!this.socket) this.connect()
    this.socket?.emit('subscribe:batch', { batch_id: batchId })
  }

  // Generic event listener
  on<T = any>(event: string, handler: EventHandler<T>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler)
  }

  // Remove event listener
  off<T = any>(event: string, handler: EventHandler<T>): void {
    const handlers = this.listeners.get(event)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.listeners.delete(event)
      }
    }
  }

  // Emit to local listeners
  private emit(event: string, data: any): void {
    const handlers = this.listeners.get(event)
    if (handlers) {
      handlers.forEach((handler) => handler(data))
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.socket?.connected || false
  }
}

// Singleton instance
export const wsClient = new WebSocketClient()

// React hook-friendly API
export function useWebSocket() {
  return {
    connect: () => wsClient.connect(),
    disconnect: () => wsClient.disconnect(),
    subscribeToJob: (jobId: string) => wsClient.subscribeToJob(jobId),
    unsubscribeFromJob: (jobId: string) => wsClient.unsubscribeFromJob(jobId),
    subscribeToBatch: (batchId: string) => wsClient.subscribeToBatch(batchId),
    on: <T = any>(event: string, handler: EventHandler<T>) => wsClient.on(event, handler),
    off: <T = any>(event: string, handler: EventHandler<T>) => wsClient.off(event, handler),
    isConnected: () => wsClient.isConnected(),
  }
}
