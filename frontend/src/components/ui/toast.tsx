'use client'

import React, { createContext, useContext, useState, useCallback } from 'react'
import { X, CheckCircle2, XCircle, AlertCircle, Info } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { ...toast, id }

    setToasts((prev) => [...prev, newToast])

    // Auto-remove after duration (default 5 seconds)
    const duration = toast.duration || 5000
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}

const TOAST_CONFIG: Record<ToastType, { icon: React.ComponentType<any>; bgColor: string; iconColor: string }> = {
  success: { icon: CheckCircle2, bgColor: 'bg-green-50 border-green-200', iconColor: 'text-green-600' },
  error: { icon: XCircle, bgColor: 'bg-red-50 border-red-200', iconColor: 'text-red-600' },
  warning: { icon: AlertCircle, bgColor: 'bg-yellow-50 border-yellow-200', iconColor: 'text-yellow-600' },
  info: { icon: Info, bgColor: 'bg-blue-50 border-blue-200', iconColor: 'text-blue-600' },
}

function ToastContainer({ toasts, removeToast }: { toasts: Toast[]; removeToast: (id: string) => void }) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-md">
      {toasts.map((toast) => {
        const config = TOAST_CONFIG[toast.type]
        const Icon = config.icon

        return (
          <div
            key={toast.id}
            className={`${config.bgColor} border rounded-lg shadow-lg p-4 flex items-start gap-3 animate-in slide-in-from-top-5 fade-in duration-300`}
            role="alert"
            aria-live="assertive"
          >
            <Icon className={`h-5 w-5 ${config.iconColor} flex-shrink-0 mt-0.5`} />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-gray-900">{toast.title}</p>
              {toast.message && (
                <p className="text-sm text-gray-600 mt-1">{toast.message}</p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-gray-400 hover:text-gray-600 flex-shrink-0"
              aria-label="Close notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
