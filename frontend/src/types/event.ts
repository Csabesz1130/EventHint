/**
 * Event/Task type definitions matching backend schema
 */

export interface Reminder {
  method: 'popup' | 'email'
  minutes: number
}

export interface Attendee {
  name: string
  email: string
}

export interface EventSource {
  message_id?: string
  provider: 'gmail' | 'outlook' | 'upload'
  confidence: number
}

export interface Event {
  id: string
  user_id: string
  type: 'event' | 'task'
  title: string
  start: string
  end?: string | null
  allday: boolean
  timezone: string
  location?: string | null
  online_url?: string | null
  notes?: string | null
  attendees: Attendee[]
  reminders: Reminder[]
  labels: string[]
  recurrence?: string | null
  status: 'pending_approval' | 'approved' | 'rejected' | 'synced' | 'error'
  confidence: number
  extraction_method?: string | null
  created_at: string
  updated_at: string
  approved_at?: string | null
  synced_at?: string | null
  external_event_id?: string | null
}

export interface EventUpdate {
  title?: string
  start?: string
  end?: string | null
  allday?: boolean
  timezone?: string
  location?: string | null
  online_url?: string | null
  notes?: string | null
  attendees?: Attendee[]
  reminders?: Reminder[]
  labels?: string[]
  recurrence?: string | null
}

export interface User {
  id: string
  email: string
  full_name?: string | null
  preferred_name?: string | null
  neptun_id?: string | null
  default_timezone: string
  auto_approve_enabled: boolean
  is_active: boolean
  created_at: string
}

