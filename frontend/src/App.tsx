import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Dashboard from './pages/Dashboard'
import Auth from './pages/Auth'
import Settings from './pages/Settings'
import EventApproval from './pages/EventApproval'

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/auth/*" element={<Auth />} />
        
        {isAuthenticated ? (
          <>
            <Route path="/" element={<Dashboard />} />
            <Route path="/event/:id" element={<EventApproval />} />
            <Route path="/settings" element={<Settings />} />
          </>
        ) : (
          <Route path="*" element={<Navigate to="/auth" replace />} />
        )}
      </Routes>
    </div>
  )
}

export default App

