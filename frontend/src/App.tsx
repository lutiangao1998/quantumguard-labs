import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Migration from './pages/Migration'
import Reports from './pages/Reports'
import TestnetScanner from './pages/TestnetScanner'
import BatchScanner from './pages/BatchScanner'
import EthereumScanner from './pages/EthereumScanner'
import History from './pages/History'
import GlobalRiskMap from './pages/GlobalRiskMap'
import HardwareWallet from './pages/HardwareWallet'
import Ecosystem from './pages/Ecosystem'
import Defense from './pages/Defense'
import CompliancePrivacy from './pages/CompliancePrivacy'
import QDeFi from './pages/QDeFi'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-950">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/analysis"  element={<Analysis />} />
            <Route path="/migration" element={<Migration />} />
            <Route path="/reports"   element={<Reports />} />
            <Route path="/testnet"   element={<TestnetScanner />} />
            <Route path="/batch"     element={<BatchScanner />} />
            <Route path="/ethereum"  element={<EthereumScanner />} />
            <Route path="/history"   element={<History />} />
            <Route path="/map"       element={<GlobalRiskMap />} />
            <Route path="/hardware_wallet" element={<HardwareWallet />} />
            <Route path="/ecosystem"       element={<Ecosystem />} />
            <Route path="/defense"         element={<Defense />} />
            <Route path="/compliance_privacy" element={<CompliancePrivacy />} />
            <Route path="/q_defi" element={<QDeFi />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
