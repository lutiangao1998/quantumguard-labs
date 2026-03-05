import { useState, useEffect } from 'react'

const RISK_BG: Record<string, string> = {
  CRITICAL: 'bg-red-900/30 border-red-500 text-red-400',
  HIGH: 'bg-orange-900/30 border-orange-500 text-orange-400',
  MEDIUM: 'bg-yellow-900/30 border-yellow-500 text-yellow-400',
  LOW: 'bg-blue-900/30 border-blue-500 text-blue-400',
  SAFE: 'bg-green-900/30 border-green-500 text-green-400',
}

interface ScanRecord {
  id: string
  address: string
  chain: string
  network: string
  risk_level: string
  risk_score: number
  balance: number
  balance_unit: string
  utxo_count: number
  is_pubkey_exposed: boolean
  scanned_at: number
  label?: string
}

interface Stats {
  total_scans: number
  total_batch_scans: number
  total_migration_plans: number
  total_audit_events: number
  risk_distribution: Record<string, number>
  latest_scan_at: number | null
}

export default function History() {
  const [records, setRecords] = useState<ScanRecord[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [chainFilter, setChainFilter] = useState('')
  const [riskFilter, setRiskFilter] = useState('')
  const [addressFilter, setAddressFilter] = useState('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const PAGE_SIZE = 20

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(page * PAGE_SIZE),
      })
      if (chainFilter) params.set('chain', chainFilter)
      if (riskFilter) params.set('risk_level', riskFilter)
      if (addressFilter) params.set('address', addressFilter)

      const [histRes, statsRes] = await Promise.all([
        fetch(`/api/blockchain/history?${params}`),
        fetch('/api/blockchain/history/stats'),
      ])
      const histData = await histRes.json()
      const statsData = await statsRes.json()

      setRecords(histData.records || [])
      setTotal(histData.total || 0)
      setStats(statsData)
    } catch (e) {
      console.error('Failed to fetch history:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [page, chainFilter, riskFilter])

  const formatDate = (ts: number) => {
    return new Date(ts * 1000).toLocaleString()
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Scan History</h1>
          <p className="text-gray-400 mt-1">All previous address scans and batch operations</p>
        </div>
        <button
          onClick={fetchHistory}
          className="text-sm text-blue-400 hover:text-blue-300 border border-blue-500 px-3 py-2 rounded-lg"
        >
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
            <div className="text-2xl font-bold text-white">{stats.total_scans}</div>
            <div className="text-xs text-gray-400 mt-1">Total Scans</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
            <div className="text-2xl font-bold text-blue-400">{stats.total_batch_scans}</div>
            <div className="text-xs text-gray-400 mt-1">Batch Sessions</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
            <div className="text-2xl font-bold text-purple-400">{stats.total_migration_plans}</div>
            <div className="text-xs text-gray-400 mt-1">Migration Plans</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
            <div className="text-2xl font-bold text-green-400">{stats.total_audit_events}</div>
            <div className="text-xs text-gray-400 mt-1">Audit Events</div>
          </div>
        </div>
      )}

      {/* Risk Distribution from History */}
      {stats && Object.keys(stats.risk_distribution).length > 0 && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Historical Risk Distribution</h2>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(stats.risk_distribution).map(([level, count]) => (
              <div key={level} className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${RISK_BG[level] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                <span className="font-semibold">{level}</span>
                <span className="text-white font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Filter by Chain</label>
            <select
              value={chainFilter}
              onChange={e => { setChainFilter(e.target.value); setPage(0) }}
              className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="">All Chains</option>
              <option value="bitcoin">Bitcoin</option>
              <option value="ethereum">Ethereum</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Filter by Risk Level</label>
            <select
              value={riskFilter}
              onChange={e => { setRiskFilter(e.target.value); setPage(0) }}
              className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
              <option value="SAFE">SAFE</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Search Address</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={addressFilter}
                onChange={e => setAddressFilter(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && fetchHistory()}
                placeholder="Partial address..."
                className="flex-1 bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 text-sm focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={() => { setPage(0); fetchHistory() }}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
              >
                Go
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Records Table */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">
            Scan Records
            <span className="text-gray-400 text-sm font-normal ml-2">({total} total)</span>
          </h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-40">
            <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-500">
            <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>No scan records yet. Start scanning addresses!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Address</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Chain</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Network</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Risk</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Balance</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Pubkey Exposed</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Scanned At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {records.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-700/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-300">
                      {r.address.length > 18 ? `${r.address.slice(0, 8)}...${r.address.slice(-6)}` : r.address}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300 capitalize">{r.chain}</td>
                    <td className="px-4 py-3 text-sm text-gray-400 capitalize">{r.network}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${RISK_BG[r.risk_level] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                        {r.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {r.balance.toFixed(6)} {r.balance_unit}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {r.is_pubkey_exposed ? (
                        <span className="text-red-400">Yes</span>
                      ) : (
                        <span className="text-green-400">No</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">{formatDate(r.scanned_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-700 flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded text-sm"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded text-sm"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
