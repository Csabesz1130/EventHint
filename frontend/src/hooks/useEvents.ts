import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { Event, EventUpdate } from '../types/event'

export function useEvents(status?: string) {
  return useQuery<Event[]>({
    queryKey: ['events', status],
    queryFn: () => api.listEvents(status),
  })
}

export function useEvent(id: string) {
  return useQuery<Event>({
    queryKey: ['event', id],
    queryFn: () => api.getEvent(id),
    enabled: !!id,
  })
}

export function useApproveEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, modifications }: { id: string; modifications?: EventUpdate }) =>
      api.approveEvent(id, modifications),
    onSuccess: () => {
      // Invalidate events list to refetch
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useRejectEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => api.rejectEvent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useUpdateEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: EventUpdate }) =>
      api.updateEvent(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['event', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useDeleteEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => api.deleteEvent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useUploadFile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => api.uploadFile(file),
    onSuccess: () => {
      // Invalidate events to show newly extracted ones
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

