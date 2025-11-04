import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ArrowLeft } from 'lucide-react'

export default function Settings() {
  const navigate = useNavigate()
  const { user } = useAuth()

  if (!user) return null

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
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Settings</h1>

          <div className="space-y-6">
            {/* Profile */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Profile</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-600">Email</label>
                  <p className="text-gray-900">{user.email}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-600">Name</label>
                  <p className="text-gray-900">{user.full_name || 'Not set'}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-600">Neptun ID</label>
                  <p className="text-gray-900">{user.neptun_id || 'Not set'}</p>
                </div>
              </div>
            </div>

            {/* Timezone */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Timezone</h2>
              <p className="text-gray-700">{user.default_timezone}</p>
            </div>

            {/* Auto-approve */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Auto-Approve</h2>
              <p className="text-gray-700">
                {user.auto_approve_enabled ? 'Enabled' : 'Disabled'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Automatically approve high-confidence events
              </p>
            </div>

            {/* Coming soon */}
            <div className="pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-500">
                More settings coming soon: notification preferences, calendar selection,
                custom extraction rules, and more.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

