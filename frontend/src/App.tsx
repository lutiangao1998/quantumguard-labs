import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Migration from './pages/Migration'
import Reports from './pages/Reports'
import TestnetScanner from './pages/TestnetScanner'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-950">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/analysis"  element={<Analysis />} />
            <Route path="/migration" element={<Migration />} />
            <Route path="/reports"   element={<Reports />} />
            <Route path="/testnet"   element={<TestnetScanner />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
