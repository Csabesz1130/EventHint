import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { User } from '../types/event'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Check for token on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setIsAuthenticated(!!token)
  }, [])

  // Fetch current user
  const { data: user, isLoading } = useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: () => api.getCurrentUser(),
    enabled: isAuthenticated,
    retry: false,
  })

  const login = (token: string) => {
    localStorage.setItem('auth_token', token)
    setIsAuthenticated(true)
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setIsAuthenticated(false)
    window.location.href = '/auth'
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
  }
}

