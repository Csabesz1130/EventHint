import type { Event, EventUpdate } from '../types/event'

interface EventEditorProps {
  event: Event
  onChange: (event: Event) => void
}

export default function EventEditor({ event, onChange }: EventEditorProps) {
  const handleChange = (field: keyof EventUpdate, value: any) => {
    onChange({ ...event, [field]: value })
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Title
        </label>
        <input
          type="text"
          value={event.title}
          onChange={(e) => handleChange('title', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date & Time
          </label>
          <input
            type="datetime-local"
            value={event.start.slice(0, 16)}
            onChange={(e) => handleChange('start', new Date(e.target.value).toISOString())}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date & Time
          </label>
          <input
            type="datetime-local"
            value={event.end ? event.end.slice(0, 16) : ''}
            onChange={(e) => handleChange('end', e.target.value ? new Date(e.target.value).toISOString() : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Location
        </label>
        <input
          type="text"
          value={event.location || ''}
          onChange={(e) => handleChange('location', e.target.value)}
          placeholder="Optional"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={event.notes || ''}
          onChange={(e) => handleChange('notes', e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  )
}

