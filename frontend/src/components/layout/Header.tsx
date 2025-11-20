'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Moon, Sun, Bell, Search } from 'lucide-react'
import { useUIStore } from '@/lib/store'
import UserProfile from '@/components/UserProfile'

export function Header() {
  const { darkMode, toggleDarkMode, commandPaletteOpen, toggleCommandPalette } = useUIStore()

  return (
    <header className="sticky top-0 z-30 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Search */}
        <Button
          variant="outline"
          className="w-64 justify-start text-muted-foreground"
          onClick={toggleCommandPalette}
        >
          <Search className="h-4 w-4 mr-2" />
          <span>Search...</span>
          <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100">
            <span className="text-xs">⌘</span>K
          </kbd>
        </Button>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
          </Button>

          <Button variant="ghost" size="icon" onClick={toggleDarkMode}>
            {darkMode ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          <Badge variant="secondary" className="ml-2">
            Production
          </Badge>

          {/* User Profile */}
          <div className="ml-4">
            <UserProfile />
          </div>
        </div>
      </div>
    </header>
  )
}
