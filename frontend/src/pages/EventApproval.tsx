import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useEvent, useApproveEvent, useRejectEvent, useUpdateEvent } from '../hooks/useEvents'
import { formatDateTime } from '../lib/utils'
import { ArrowLeft, CheckCircle, XCircle, Save } from 'lucide-react'
import EventEditor from '../components/EventEditor'

export default function EventApproval() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: event, isLoading } = useEvent(id!)
  const approveEvent = useApproveEvent()
  const rejectEvent = useRejectEvent()
  const updateEvent = useUpdateEvent()
  
  const [isEditing, setIsEditing] = useState(false)
  const [editedEvent, setEditedEvent] = useState(event)

  if (isLoading || !event) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const handleApprove = async () => {
    try {
      await approveEvent.mutateAsync({ id: event.id })
      navigate('/')
    } catch (error) {
      console.error('Approve failed:', error)
    }
  }

  const handleReject = async () => {
    try {
      await rejectEvent.mutateAsync(event.id)
      navigate('/')
    } catch (error) {
      console.error('Reject failed:', error)
    }
  }

  const handleSave = async () => {
    if (!editedEvent) return
    
    try {
      await updateEvent.mutateAsync({
        id: event.id,
        data: {
          title: editedEvent.title,
          start: editedEvent.start,
          end: editedEvent.end,
          location: editedEvent.location,
          notes: editedEvent.notes,
          reminders: editedEvent.reminders,
        },
      })
      setIsEditing(false)
    } catch (error) {
      console.error('Save failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Review Event
            </h1>
            <p className="text-gray-600">
              Extracted with {Math.round(event.confidence * 100)}% confidence
            </p>
          </div>

          {isEditing ? (
            <EventEditor
              event={editedEvent || event}
              onChange={setEditedEvent}
            />
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <p className="text-lg text-gray-900">{event.title}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date & Time
                </label>
                <p className="text-lg text-gray-900">{formatDateTime(event.start)}</p>
              </div>

              {event.location && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <p className="text-lg text-gray-900">{event.location}</p>
                </div>
              )}

              {event.notes && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <p className="text-gray-700 whitespace-pre-wrap">{event.notes}</p>
                </div>
              )}

              {event.reminders.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reminders
                  </label>
                  <ul className="list-disc list-inside text-gray-700">
                    {event.reminders.map((reminder, i) => (
                      <li key={i}>
                        {reminder.minutes} minutes before ({reminder.method})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="mt-8 flex gap-3">
            {isEditing ? (
              <>
                <button
                  onClick={handleSave}
                  disabled={updateEvent.isPending}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  <Save className="w-5 h-5" />
                  Save Changes
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false)
                    setEditedEvent(event)
                  }}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleApprove}
                  disabled={approveEvent.isPending}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  <CheckCircle className="w-5 h-5" />
                  {approveEvent.isPending ? 'Approving...' : 'Approve & Add to Calendar'}
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Edit
                </button>
                <button
                  onClick={handleReject}
                  disabled={rejectEvent.isPending}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

