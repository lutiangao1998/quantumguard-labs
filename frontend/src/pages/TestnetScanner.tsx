import { useState } from 'react'
import { scanTestnetAddress, getBlockchainStatus } from '../api/client'
import { Wifi, Search, ExternalLink } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#f44336', HIGH: '#ff9800', MEDIUM: '#ffc107', LOW: '#4caf50', SAFE: '#2196f3',
}

const SAMPLE_ADDRESSES = [
  'tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx',
  'tb1q0kfhgkxz4j3fqjpkxnhm9q9r3l8v4p5w3jkzq',
  'tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7',
]

export default function TestnetScanner() {
  const [address, setAddress] = useState('')
  const [result, setResult] = useState<any>(null)
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [statusLoading, setStatusLoading] = useState(false)

  const checkStatus = async () => {
    setStatusLoading(true)
    try { setStatus(await getBlockchainStatus()) }
    catch (e) { console.error(e) }
    finally { setStatusLoading(false) }
  }

  const scan = async () => {
    if (!address.trim()) return
    setLoading(true)
    try { setResult(await scanTestnetAddress(address.trim())) }
    catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Bitcoin Testnet Scanner</h1>
        <p className="text-slate-400 text-sm mt-1">Scan real Bitcoin testnet addresses for quantum exposure using Blockstream API</p>
      </div>

      {/* Network status */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-300">Network Status</h2>
          <button
            onClick={checkStatus} disabled={statusLoading}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded-lg"
          >
            <Wifi size={12} />
            {statusLoading ? 'Checking...' : 'Check Status'}
          </button>
        </div>
        {status ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Network',   value: status.network },
              { label: 'Connector', value: status.connector_type },
              { label: 'Status',    value: status.status },
              { label: 'API',       value: status.api_url ?? 'N/A' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-700 rounded-lg p-3">
                <div className="text-xs text-slate-400">{label}</div>
                <div className="text-sm text-white font-mono mt-0.5 truncate">{value}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">Click "Check Status" to verify Blockstream Testnet API connectivity.</p>
        )}
      </div>

      {/* Address scanner */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">Scan Testnet Address</h2>
        <div className="flex gap-3">
          <input
            value={address} onChange={e => setAddress(e.target.value)}
            placeholder="Enter Bitcoin testnet address (tb1q..., m..., n..., 2...)"
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono placeholder-slate-500"
            onKeyDown={e => e.key === 'Enter' && scan()}
          />
          <button
            onClick={scan} disabled={loading || !address.trim()}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm rounded-lg"
          >
            <Search size={14} />
            {loading ? 'Scanning...' : 'Scan'}
          </button>
        </div>

        {/* Sample addresses */}
        <div>
          <div className="text-xs text-slate-400 mb-2">Sample testnet addresses:</div>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_ADDRESSES.map(addr => (
              <button
                key={addr}
                onClick={() => setAddress(addr)}
                className="text-xs font-mono text-cyan-400 hover:text-cyan-300 bg-slate-700 px-2 py-1 rounded truncate max-w-xs"
              >
                {addr.slice(0, 24)}...
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-24">
          <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-3 text-slate-400 text-sm">Querying Blockstream Testnet API...</span>
        </div>
      )}

      {result && !loading && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-300">Scan Results</h2>
            <a
              href={`https://blockstream.info/testnet/address/${address}`}
              target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300"
            >
              View on Blockstream <ExternalLink size={10} />
            </a>
          </div>

          {result.utxo_count === 0 ? (
            <div className="text-sm text-slate-400 text-center py-6">
              No UTXOs found for this address on Bitcoin Testnet.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-700 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold text-white">{result.utxo_count}</div>
                  <div className="text-xs text-slate-400">UTXOs Found</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold text-white">{result.total_value_btc?.toFixed(6)}</div>
                  <div className="text-xs text-slate-400">Total BTC</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold" style={{ color: RISK_COLORS[result.risk_level ?? 'SAFE'] }}>
                    {result.risk_level ?? 'SAFE'}
                  </div>
                  <div className="text-xs text-slate-400">Risk Level</div>
                </div>
              </div>

              {result.utxos && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs border-b border-slate-700">
                        <th className="text-left py-2 pr-4">TXID</th>
                        <th className="text-right py-2 pr-4">Vout</th>
                        <th className="text-right py-2 pr-4">Value (BTC)</th>
                        <th className="text-left py-2">Script Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.utxos.map((u: any, i: number) => (
                        <tr key={i} className="border-b border-slate-700/50">
                          <td className="py-2 pr-4 font-mono text-xs text-slate-300">{u.txid?.slice(0, 20)}...</td>
                          <td className="py-2 pr-4 text-right text-slate-300">{u.vout}</td>
                          <td className="py-2 pr-4 text-right text-slate-200">{u.value_btc?.toFixed(8)}</td>
                          <td className="py-2 text-slate-300">{u.script_type}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
