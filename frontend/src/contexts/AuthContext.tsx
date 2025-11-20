"use client"

import React, { createContext, useContext, useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  email: string
  username?: string
  full_name?: string
  role: string
  account_status: string
  jobs_created_count: number
  jobs_quota: number
  tokens_used: number
  tokens_quota: number
  last_login?: string
  created_at: string
}

interface AuthContextType {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string, username?: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshTokenValue, setRefreshTokenValue] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Load tokens from localStorage on mount
  useEffect(() => {
    const storedAccessToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')

    if (storedAccessToken && storedUser) {
      setAccessToken(storedAccessToken)
      setRefreshTokenValue(storedRefreshToken)
      setUser(JSON.parse(storedUser))
    }

    setIsLoading(false)
  }, [])

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!accessToken || !refreshTokenValue) return

    // Refresh token every 25 minutes (tokens expire in 30 minutes)
    const interval = setInterval(() => {
      refreshToken()
    }, 25 * 60 * 1000)

    return () => clearInterval(interval)
  }, [accessToken, refreshTokenValue])

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()

    // Store tokens and user
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))

    setAccessToken(data.access_token)
    setRefreshTokenValue(data.refresh_token)
    setUser(data.user)

    // Redirect to dashboard
    router.push('/')
  }

  const register = async (
    email: string,
    password: string,
    fullName?: string,
    username?: string
  ) => {
    const response = await fetch(`${API_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        username,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    const data = await response.json()

    // Store tokens and user
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))

    setAccessToken(data.access_token)
    setRefreshTokenValue(data.refresh_token)
    setUser(data.user)

    // Redirect to dashboard
    router.push('/')
  }

  const logout = () => {
    // Clear tokens
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')

    setAccessToken(null)
    setRefreshTokenValue(null)
    setUser(null)

    // Redirect to login
    router.push('/login')
  }

  const refreshToken = async () => {
    if (!refreshTokenValue) return

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        // Refresh failed, logout user
        logout()
        return
      }

      const data = await response.json()

      // Update tokens
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.user))

      setAccessToken(data.access_token)
      setRefreshTokenValue(data.refresh_token)
      setUser(data.user)
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
