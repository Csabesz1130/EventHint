import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useEvents, useUploadFile, useProcessUrl } from '../hooks/useEvents'
import EventCard from '../components/EventCard'
import { Upload, LogOut, Settings as SettingsIcon, Link as LinkIcon } from 'lucide-react'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const { data: events, isLoading } = useEvents('pending_approval')
  const uploadFile = useUploadFile()
  const processUrl = useProcessUrl()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [url, setUrl] = useState('')

  const handleFileUpload = async (file: File) => {
    try {
      await uploadFile.mutateAsync(file)
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    try {
      await processUrl.mutateAsync(url)
      setUrl('')
    } catch (error) {
      console.error('URL processing failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">EventHint</h1>
              <p className="text-sm text-gray-500">
                Welcome back, {user?.full_name || user?.email}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/settings"
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              >
                <SettingsIcon className="w-5 h-5" />
              </Link>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              >
                <LogOut className="w-4 h-4" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <div className="mb-8 grid gap-6 md:grid-cols-2">
          {/* File Upload */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 bg-white hover:border-gray-400'
            }`}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Upload a file
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Drop an image, PDF, or email file here
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadFile.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadFile.isPending ? 'Uploading...' : 'Choose File'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept="image/*,.pdf,.eml,.msg"
              onChange={handleFileInput}
            />
          </div>

          {/* URL Processing */}
          <div className="border-2 border-dashed rounded-lg p-8 text-center transition-colors border-gray-300 bg-white hover:border-gray-400">
            <LinkIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Process a website
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Enter a URL to extract events from a webpage
            </p>
            <form onSubmit={handleUrlSubmit} className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/event"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={processUrl.isPending}
              />
              <button
                type="submit"
                disabled={processUrl.isPending || !url.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {processUrl.isPending ? 'Processing...' : 'Process'}
              </button>
            </form>
          </div>
        </div>

        {/* Pending Events */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Pending Approvals
            {events && events.length > 0 && (
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({events.length})
              </span>
            )}
          </h2>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-500">Loading events...</p>
            </div>
          ) : events && events.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {events.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg p-12 text-center border border-gray-200">
              <p className="text-gray-500">
                No pending events. Upload a file or connect your email to get started.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

