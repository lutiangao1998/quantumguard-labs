import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
  SAFE: '#22c55e',
}

const RISK_BG: Record<string, string> = {
  CRITICAL: 'bg-red-900/30 border-red-500 text-red-400',
  HIGH: 'bg-orange-900/30 border-orange-500 text-orange-400',
  MEDIUM: 'bg-yellow-900/30 border-yellow-500 text-yellow-400',
  LOW: 'bg-blue-900/30 border-blue-500 text-blue-400',
  SAFE: 'bg-green-900/30 border-green-500 text-green-400',
}

interface AddressResult {
  address: string
  utxo_count?: number
  total_btc?: number
  balance_eth?: number
  risk_level: string
  quantum_readiness_score?: number
  error?: string
}

interface BatchSummary {
  chain: string
  network: string
  total_addresses: number
  scanned: number
  errors: number
  total_btc?: number
  total_eth?: number
  at_risk_btc?: number
  at_risk_eth?: number
  risk_summary: Record<string, number>
  quantum_readiness_score: number
}

export default function BatchScanner() {
  const [addressInput, setAddressInput] = useState('')
  const [chain, setChain] = useState<'bitcoin' | 'ethereum'>('bitcoin')
  const [network, setNetwork] = useState('testnet')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<AddressResult[]>([])
  const [summary, setSummary] = useState<BatchSummary | null>(null)
  const [errors, setErrors] = useState<{ address: string; error: string }[]>([])

  const parseAddresses = () => {
    return addressInput
      .split(/[\n,;]+/)
      .map(a => a.trim())
      .filter(a => a.length > 0)
  }

  const handleScan = async () => {
    const addresses = parseAddresses()
    if (addresses.length === 0) return
    if (addresses.length > 50) {
      alert('Maximum 50 addresses per batch. Please reduce the list.')
      return
    }

    setLoading(true)
    setResults([])
    setSummary(null)
    setErrors([])

    try {
      const res = await fetch('/api/blockchain/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ addresses, chain, network, save_history: true }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Batch scan failed')
      setResults(data.results || [])
      setSummary(data.summary || null)
      setErrors(data.errors || [])
    } catch (e: any) {
      alert(`Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const chartData = summary
    ? Object.entries(summary.risk_summary).map(([level, count]) => ({ level, count }))
    : []

  const exportCSV = () => {
    if (!results.length) return
    const header = 'Address,Risk Level,Readiness Score,Balance,UTXOs\n'
    const rows = results.map(r =>
      `${r.address},${r.risk_level},${r.quantum_readiness_score ?? ''},${r.total_btc ?? r.balance_eth ?? 0},${r.utxo_count ?? 0}`
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch_scan_${Date.now()}.csv`
    a.click()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Batch Scanner</h1>
        <p className="text-gray-400 mt-1">
          Scan up to 50 addresses at once. Paste one address per line, or separate with commas.
        </p>
      </div>

      {/* Input Panel */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Chain selector */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Chain</label>
            <div className="flex gap-2">
              {(['bitcoin', 'ethereum'] as const).map(c => (
                <button
                  key={c}
                  onClick={() => {
                    setChain(c)
                    setNetwork(c === 'bitcoin' ? 'testnet' : 'mainnet')
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                    chain === c
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {c === 'bitcoin' ? '₿ Bitcoin' : 'Ξ Ethereum'}
                </button>
              ))}
            </div>
          </div>

          {/* Network selector */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Network</label>
            <select
              value={network}
              onChange={e => setNetwork(e.target.value)}
              className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-blue-500"
            >
              {chain === 'bitcoin' ? (
                <>
                  <option value="testnet">Testnet</option>
                  <option value="mainnet">Mainnet</option>
                </>
              ) : (
                <>
                  <option value="mainnet">Mainnet</option>
                  <option value="goerli">Goerli Testnet</option>
                </>
              )}
            </select>
          </div>
        </div>

        {/* Address input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Addresses <span className="text-gray-500">(one per line or comma-separated, max 50)</span>
          </label>
          <textarea
            value={addressInput}
            onChange={e => setAddressInput(e.target.value)}
            rows={8}
            placeholder={
              chain === 'bitcoin'
                ? 'tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx\ntb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7\n...'
                : '0x742d35Cc6634C0532925a3b8D4C9C8f3b2b3e4f5\n0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045\n...'
            }
            className="w-full bg-gray-900 text-white rounded-lg px-4 py-3 border border-gray-600 focus:outline-none focus:border-blue-500 font-mono text-sm resize-none"
          />
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-500">
              {parseAddresses().length} address{parseAddresses().length !== 1 ? 'es' : ''} detected
            </span>
            <button
              onClick={() => setAddressInput('')}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Clear
            </button>
          </div>
        </div>

        <button
          onClick={handleScan}
          disabled={loading || parseAddresses().length === 0}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Scanning {parseAddresses().length} addresses...
            </span>
          ) : (
            `Scan ${parseAddresses().length > 0 ? parseAddresses().length + ' ' : ''}Addresses`
          )}
        </button>
      </div>

      {/* Summary */}
      {summary && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Batch Summary</h2>
            <button
              onClick={exportCSV}
              className="text-sm text-blue-400 hover:text-blue-300 border border-blue-500 px-3 py-1 rounded-lg"
            >
              Export CSV
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-900 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">{summary.scanned}</div>
              <div className="text-xs text-gray-400 mt-1">Addresses Scanned</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-400">
                {summary.quantum_readiness_score.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400 mt-1">Quantum Readiness</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">
                {summary.total_btc !== undefined
                  ? `${summary.total_btc.toFixed(4)} BTC`
                  : `${(summary.total_eth || 0).toFixed(4)} ETH`}
              </div>
              <div className="text-xs text-gray-400 mt-1">Total Balance</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-400">
                {summary.at_risk_btc !== undefined
                  ? `${summary.at_risk_btc.toFixed(4)} BTC`
                  : `${(summary.at_risk_eth || 0).toFixed(4)} ETH`}
              </div>
              <div className="text-xs text-gray-400 mt-1">At-Risk Balance</div>
            </div>
          </div>

          {/* Risk distribution chart */}
          {chartData.length > 0 && (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="level" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#f9fafb' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell key={entry.level} fill={RISK_COLORS[entry.level] || '#6b7280'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">Individual Results</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Address</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Risk Level</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Readiness</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Balance</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">UTXOs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {results.map((r, i) => (
                  <tr key={i} className="hover:bg-gray-700/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-300">
                      {r.address.length > 20 ? `${r.address.slice(0, 10)}...${r.address.slice(-8)}` : r.address}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${RISK_BG[r.risk_level] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                        {r.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {r.quantum_readiness_score !== undefined ? `${r.quantum_readiness_score.toFixed(1)}%` : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {r.total_btc !== undefined ? `${r.total_btc.toFixed(6)} BTC` : `${(r.balance_eth || 0).toFixed(6)} ETH`}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {r.utxo_count ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-red-900/20 border border-red-500 rounded-xl p-4">
          <h3 className="text-red-400 font-semibold mb-2">Failed Addresses ({errors.length})</h3>
          {errors.map((e, i) => (
            <div key={i} className="text-sm text-red-300 font-mono">
              {e.address}: {e.error}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
