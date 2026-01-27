import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Monitors } from './pages/Monitors'
import { Scanner } from './pages/Scanner'
import { Quarantine } from './pages/Quarantine'
import { AIAssistant } from './pages/AIAssistant'
import { Logs } from './pages/Logs'
import { Settings } from './pages/Settings'
import License from './pages/License'
import Purchase from './pages/Purchase'
import Login from './pages/Login'
import Register from './pages/Register'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="monitors" element={<Monitors />} />
            <Route path="scanner" element={<Scanner />} />
            <Route path="quarantine" element={<Quarantine />} />
            <Route path="ai" element={<AIAssistant />} />
            <Route path="logs" element={<Logs />} />
            <Route path="settings" element={<Settings />} />
            <Route path="license" element={<License />} />
            <Route path="purchase" element={<Purchase />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}

export default App
