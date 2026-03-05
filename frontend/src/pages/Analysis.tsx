import { useState } from 'react'
import { analyzePortfolio, type AnalysisResponse } from '../api/client'
import { Search, Download } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#f44336', HIGH: '#ff9800', MEDIUM: '#ffc107', LOW: '#4caf50', SAFE: '#2196f3',
}

export default function Analysis() {
  const [utxoCount, setUtxoCount] = useState(100)
  const [data, setData] = useState<AnalysisResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')

  const run = async () => {
    setLoading(true)
    try {
      const res = await analyzePortfolio({ utxo_count: utxoCount })
      setData(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const filtered = (data?.assessments ?? []).filter(a => {
    const matchFilter = filter === 'ALL' || a.risk_level === filter
    const matchSearch = !search || a.address.includes(search) || a.txid.includes(search)
    return matchFilter && matchSearch
  })

  const exportCSV = () => {
    if (!data) return
    const rows = [
      ['TXID', 'Address', 'Script Type', 'Value BTC', 'Risk Level', 'Risk Score', 'Priority'],
      ...data.assessments.map(a => [a.txid, a.address, a.script_type, a.value_btc, a.risk_level, a.risk_score, a.migration_priority]),
    ]
    const csv = rows.map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'risk_analysis.csv'; a.click()
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Quantum Risk Analysis</h1>
        <p className="text-slate-400 text-sm mt-1">Scan Bitcoin UTXOs and classify quantum exposure</p>
      </div>

      {/* Controls */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs text-slate-400 mb-1">UTXO Sample Size</label>
          <input
            type="number" min={10} max={500} value={utxoCount}
            onChange={e => setUtxoCount(+e.target.value)}
            className="w-32 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
          />
        </div>
        <button
          onClick={run} disabled={loading}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
        >
          {loading ? 'Scanning...' : 'Run Analysis'}
        </button>
        {data && (
          <button onClick={exportCSV} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg flex items-center gap-2">
            <Download size={14} /> Export CSV
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-3 text-slate-400">Analyzing {utxoCount} UTXOs...</span>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE'] as const).map(level => {
              const count = data[`${level.toLowerCase()}_count` as keyof AnalysisResponse] as number
              return (
                <div key={level} className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold" style={{ color: RISK_COLORS[level] }}>{count}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{level}</div>
                </div>
              )
            })}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-cyan-400">{data.quantum_readiness_score.toFixed(1)}</div>
              <div className="text-xs text-slate-400 mt-0.5">QR Score</div>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="flex gap-2">
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE'].map(f => (
                <button
                  key={f} onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                    filter === f
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-slate-700 rounded-lg px-3 py-1.5 flex-1 max-w-xs">
              <Search size={14} className="text-slate-400" />
              <input
                placeholder="Search address or txid..."
                value={search} onChange={e => setSearch(e.target.value)}
                className="bg-transparent text-sm text-white placeholder-slate-500 outline-none flex-1"
              />
            </div>
          </div>

          {/* Table */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-900">
                  <tr className="text-slate-400 text-xs">
                    <th className="text-left px-4 py-3">TXID</th>
                    <th className="text-left px-4 py-3">Address</th>
                    <th className="text-left px-4 py-3">Script</th>
                    <th className="text-right px-4 py-3">Value (BTC)</th>
                    <th className="text-center px-4 py-3">Score</th>
                    <th className="text-left px-4 py-3">Risk Level</th>
                    <th className="text-left px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 50).map((a, i) => (
                    <tr key={i} className="border-t border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-2.5 font-mono text-xs text-slate-300">{a.txid.slice(0, 12)}...</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-slate-300">{a.address.slice(0, 16)}...</td>
                      <td className="px-4 py-2.5 text-slate-300 text-xs">{a.script_type}</td>
                      <td className="px-4 py-2.5 text-right text-slate-200 font-mono text-xs">{a.value_btc.toFixed(6)}</td>
                      <td className="px-4 py-2.5 text-center">
                        <div className="flex items-center justify-center">
                          <div className="w-16 bg-slate-700 rounded-full h-1.5">
                            <div
                              className="h-1.5 rounded-full"
                              style={{ width: `${a.risk_score}%`, backgroundColor: RISK_COLORS[a.risk_level] }}
                            />
                          </div>
                          <span className="ml-2 text-xs text-slate-400">{a.risk_score}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className="px-2 py-0.5 rounded text-xs font-semibold"
                          style={{ backgroundColor: RISK_COLORS[a.risk_level] + '25', color: RISK_COLORS[a.risk_level] }}
                        >
                          {a.risk_level}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-xs text-slate-400 max-w-xs truncate">{a.risk_reasons[0]?.slice(0, 50)}...</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filtered.length > 50 && (
              <div className="px-4 py-3 text-xs text-slate-400 border-t border-slate-700">
                Showing 50 of {filtered.length} results. Export CSV to see all.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
