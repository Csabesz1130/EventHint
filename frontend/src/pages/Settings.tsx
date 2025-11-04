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

            {/* Approval Preview Mode */}
            <div className="pt-6 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Event Approval Preview
              </h2>
              <p className="text-sm text-gray-600 mb-3">
                Choose how you want to preview events before approving them
              </p>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="approvalPreview"
                    value="modal"
                    checked={approvalPreviewMode === 'modal'}
                    onChange={(e) => setApprovalPreviewMode(e.target.value as any)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">Modal Preview</div>
                    <div className="text-sm text-gray-500">
                      Show event details in a popup before confirming
                    </div>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="approvalPreview"
                    value="inline"
                    checked={approvalPreviewMode === 'inline'}
                    onChange={(e) => setApprovalPreviewMode(e.target.value as any)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">Inline Preview</div>
                    <div className="text-sm text-gray-500">
                      Expand event card to show full details
                    </div>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="approvalPreview"
                    value="none"
                    checked={approvalPreviewMode === 'none'}
                    onChange={(e) => setApprovalPreviewMode(e.target.value as any)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">No Preview</div>
                    <div className="text-sm text-gray-500">
                      Approve immediately without preview
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {/* Link Handling Mode */}
            <div className="pt-6 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Link Handling
              </h2>
              <p className="text-sm text-gray-600 mb-3">
                Choose how links should be handled in emails and events
              </p>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="linkHandling"
                    value="render_in_email"
                    checked={linkHandlingMode === 'render_in_email'}
                    onChange={(e) => setLinkHandlingMode(e.target.value as any)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">Render in Email Only</div>
                    <div className="text-sm text-gray-500">
                      Show clickable links in email display
                    </div>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="linkHandling"
                    value="add_to_event"
                    checked={linkHandlingMode === 'add_to_event'}
                    onChange={(e) => setLinkHandlingMode(e.target.value as any)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">Add to Event</div>
                    <div className="text-sm text-gray-500">
                      Extract links and add them to event details
                    </div>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="linkHandling"
                    value="both"
                    checked={linkHandlingMode === 'both'}
                    onChange={(e) => setLinkHandlingMode(e.target.value as any)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <div className="font-medium text-gray-900">Both</div>
                    <div className="text-sm text-gray-500">
                      Render in email and add to event details
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {/* Save button */}
            <div className="pt-6 border-t border-gray-200">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="w-5 h-5" />
                {isSaving ? 'Saving...' : 'Save Settings'}
              </button>
              {message && (
                <p className={`mt-3 text-sm ${message.includes('success') ? 'text-green-600' : 'text-red-600'}`}>
                  {message}
                </p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

