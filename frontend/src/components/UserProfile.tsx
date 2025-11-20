"use client"

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'

export default function UserProfile() {
  const { user, isAuthenticated, logout } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center space-x-2">
        <Link
          href="/login"
          className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
        >
          Sign Up
        </Link>
      </div>
    )
  }

  const quotaPercentage = Math.round((user.jobs_created_count / user.jobs_quota) * 100)
  const tokensPercentage = Math.round((user.tokens_used / user.tokens_quota) * 100)

  return (
    <div className="relative">
      {/* Profile Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-100 transition"
      >
        {/* Avatar */}
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
          {user.full_name ? user.full_name[0].toUpperCase() : user.email[0].toUpperCase()}
        </div>

        {/* User Info */}
        <div className="text-left hidden md:block">
          <div className="text-sm font-medium text-gray-900">
            {user.full_name || user.username || user.email.split('@')[0]}
          </div>
          <div className="text-xs text-gray-500 capitalize">{user.role}</div>
        </div>

        {/* Dropdown Arrow */}
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

          {/* Menu */}
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 z-20">
            {/* User Header */}
            <div className="p-4 border-b border-gray-100">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
                  {user.full_name ? user.full_name[0].toUpperCase() : user.email[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-gray-900 truncate">
                    {user.full_name || user.username || 'User'}
                  </div>
                  <div className="text-xs text-gray-500 truncate">{user.email}</div>
                  <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-1 capitalize">
                    {user.role}
                  </div>
                </div>
              </div>
            </div>

            {/* Quota Stats */}
            <div className="p-4 space-y-3 bg-gray-50">
              <div className="text-xs font-medium text-gray-700 mb-2">Usage This Month</div>

              {/* Jobs Quota */}
              <div>
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Jobs</span>
                  <span>
                    {user.jobs_created_count}/{user.jobs_quota}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      quotaPercentage > 80
                        ? 'bg-red-500'
                        : quotaPercentage > 50
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(quotaPercentage, 100)}%` }}
                  />
                </div>
              </div>

              {/* Tokens Quota */}
              <div>
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Tokens</span>
                  <span>
                    {(user.tokens_used / 1000).toFixed(1)}k/{(user.tokens_quota / 1000).toFixed(0)}k
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      tokensPercentage > 80
                        ? 'bg-red-500'
                        : tokensPercentage > 50
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(tokensPercentage, 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Menu Items */}
            <div className="py-2">
              <Link
                href="/settings"
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition"
                onClick={() => setIsOpen(false)}
              >
                <svg className="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </Link>

              {user.role === 'admin' && (
                <Link
                  href="/admin"
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition"
                  onClick={() => setIsOpen(false)}
                >
                  <svg className="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                    />
                  </svg>
                  Admin Panel
                </Link>
              )}
            </div>

            {/* Logout */}
            <div className="border-t border-gray-100">
              <button
                onClick={() => {
                  setIsOpen(false)
                  logout()
                }}
                className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition"
              >
                <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  />
                </svg>
                Sign Out
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
