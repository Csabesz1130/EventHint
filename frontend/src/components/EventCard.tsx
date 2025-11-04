import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApproveEvent, useRejectEvent } from '../hooks/useEvents'
import { formatDateTime, cn } from '../lib/utils'
import { Calendar, MapPin, Clock, CheckCircle, XCircle, Edit, ExternalLink } from 'lucide-react'
import type { Event } from '../types/event'

interface EventCardProps {
  event: Event
}

export default function EventCard({ event }: EventCardProps) {
  const navigate = useNavigate()
  const approveEvent = useApproveEvent()
  const rejectEvent = useRejectEvent()
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)

  const handleApprove = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsApproving(true)
    try {
      await approveEvent.mutateAsync({ id: event.id })
    } catch (error) {
      console.error('Approve failed:', error)
    } finally {
      setIsApproving(false)
    }
  }

  const handleReject = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsRejecting(true)
    try {
      await rejectEvent.mutateAsync(event.id)
    } catch (error) {
      console.error('Reject failed:', error)
    } finally {
      setIsRejecting(false)
    }
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigate(`/event/${event.id}`)
  }

  // Confidence color
  const confidenceColor =
    event.confidence >= 0.8
      ? 'text-green-600 bg-green-50'
      : event.confidence >= 0.5
      ? 'text-yellow-600 bg-yellow-50'
      : 'text-red-600 bg-red-50'

  // Label colors
  const labelColors: Record<string, string> = {
    exam: 'bg-red-100 text-red-800',
    meeting: 'bg-blue-100 text-blue-800',
    deadline: 'bg-orange-100 text-orange-800',
    flight: 'bg-purple-100 text-purple-800',
    travel: 'bg-indigo-100 text-indigo-800',
  }

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={handleEdit}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 flex-1 pr-2">
          {event.title}
        </h3>
        <span
          className={cn(
            'text-xs px-2 py-1 rounded-full font-medium',
            confidenceColor
          )}
        >
          {Math.round(event.confidence * 100)}%
        </span>
      </div>

      {/* Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="w-4 h-4" />
          <span>{formatDateTime(event.start)}</span>
        </div>

        {event.location && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <MapPin className="w-4 h-4" />
            <span>{event.location}</span>
          </div>
        )}

        {event.online_url && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <ExternalLink className="w-4 h-4" />
            <a
              href={event.online_url}
              onClick={(e) => e.stopPropagation()}
              className="hover:underline truncate"
            >
              Online meeting
            </a>
          </div>
        )}

        {event.reminders.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>{event.reminders.length} reminder(s)</span>
          </div>
        )}
      </div>

      {/* Labels */}
      {event.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {event.labels.map((label) => (
            <span
              key={label}
              className={cn(
                'text-xs px-2 py-1 rounded-full font-medium',
                labelColors[label] || 'bg-gray-100 text-gray-800'
              )}
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* Notes preview */}
      {event.notes && (
        <p className="text-sm text-gray-500 mb-4 line-clamp-2">
          {event.notes}
        </p>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleApprove}
          disabled={isApproving}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <CheckCircle className="w-4 h-4" />
          {isApproving ? 'Approving...' : 'Approve'}
        </button>

        <button
          onClick={handleEdit}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <Edit className="w-4 h-4" />
        </button>

        <button
          onClick={handleReject}
          disabled={isRejecting}
          className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <XCircle className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

