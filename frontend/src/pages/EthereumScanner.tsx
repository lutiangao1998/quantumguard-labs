import { useState } from 'react'

const RISK_BG: Record<string, string> = {
  CRITICAL: 'bg-red-900/30 border-red-500 text-red-400',
  HIGH: 'bg-orange-900/30 border-orange-500 text-orange-400',
  MEDIUM: 'bg-yellow-900/30 border-yellow-500 text-yellow-400',
  LOW: 'bg-blue-900/30 border-blue-500 text-blue-400',
  SAFE: 'bg-green-900/30 border-green-500 text-green-400',
}

const SAMPLE_ETH_ADDRESSES = [
  '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  // Vitalik Buterin
  '0x742d35Cc6634C0532925a3b8D4C9C8f3b2b3e4f5',
  '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',  // Binance cold wallet
]

interface EthResult {
  address: string
  network: string
  risk_level: string
  risk_score: number
  risk_reasons: string[]
  balance_eth: number
  balance_usd_approx: number
  is_contract: boolean
  is_pubkey_exposed: boolean
  tx_count: number
  account_type: string
  quantum_readiness_score: number
  recommendations: string[]
}

export default function EthereumScanner() {
  const [address, setAddress] = useState('')
  const [network, setNetwork] = useState('mainnet')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<EthResult | null>(null)
  const [error, setError] = useState('')

  const handleScan = async () => {
    if (!address.trim()) return
    setLoading(true)
    setResult(null)
    setError('')

    try {
      const res = await fetch(
        `/api/blockchain/ethereum/scan?address=${encodeURIComponent(address)}&network=${network}&save_history=true`
      )
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Scan failed')
      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="text-purple-400">Ξ</span> Ethereum Quantum Scanner
        </h1>
        <p className="text-gray-400 mt-1">
          Analyze Ethereum addresses for quantum vulnerability — EOA exposure, transaction history, and public key risk.
        </p>
      </div>

      {/* Input Panel */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 space-y-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-300 mb-2">Ethereum Address</label>
            <input
              type="text"
              value={address}
              onChange={e => setAddress(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleScan()}
              placeholder="0x742d35Cc6634C0532925a3b8D4C9C8f3b2b3e4f5"
              className="w-full bg-gray-900 text-white rounded-lg px-4 py-3 border border-gray-600 focus:outline-none focus:border-purple-500 font-mono text-sm"
            />
          </div>
          <div className="w-36">
            <label className="block text-sm font-medium text-gray-300 mb-2">Network</label>
            <select
              value={network}
              onChange={e => setNetwork(e.target.value)}
              className="w-full bg-gray-700 text-white rounded-lg px-3 py-3 border border-gray-600 focus:outline-none focus:border-purple-500"
            >
              <option value="mainnet">Mainnet</option>
              <option value="goerli">Goerli</option>
            </select>
          </div>
        </div>

        {/* Sample addresses */}
        <div>
          <span className="text-xs text-gray-500 mr-2">Sample addresses:</span>
          {SAMPLE_ETH_ADDRESSES.map(addr => (
            <button
              key={addr}
              onClick={() => setAddress(addr)}
              className="text-xs text-purple-400 hover:text-purple-300 font-mono mr-3"
            >
              {addr.slice(0, 10)}...
            </button>
          ))}
        </div>

        <button
          onClick={handleScan}
          disabled={loading || !address.trim()}
          className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Analyzing Ethereum Address...
            </span>
          ) : 'Scan for Quantum Risk'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-500 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          {/* Risk Banner */}
          <div className={`rounded-xl p-6 border-2 ${RISK_BG[result.risk_level]}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium opacity-70 mb-1">Quantum Risk Assessment</div>
                <div className="text-3xl font-bold">{result.risk_level}</div>
                <div className="font-mono text-sm mt-1 opacity-70">{result.address}</div>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold">{result.quantum_readiness_score.toFixed(1)}%</div>
                <div className="text-sm opacity-70">Quantum Readiness Score</div>
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
              <div className="text-xl font-bold text-white">{result.balance_eth.toFixed(4)} ETH</div>
              <div className="text-xs text-gray-400 mt-1">Balance</div>
            </div>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
              <div className="text-xl font-bold text-white">{result.tx_count.toLocaleString()}</div>
              <div className="text-xs text-gray-400 mt-1">Transactions</div>
            </div>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
              <div className={`text-xl font-bold ${result.is_pubkey_exposed ? 'text-red-400' : 'text-green-400'}`}>
                {result.is_pubkey_exposed ? 'Exposed' : 'Hidden'}
              </div>
              <div className="text-xs text-gray-400 mt-1">Public Key</div>
            </div>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
              <div className="text-xl font-bold text-white capitalize">{result.account_type}</div>
              <div className="text-xs text-gray-400 mt-1">Account Type</div>
            </div>
          </div>

          {/* Risk Reasons */}
          {result.risk_reasons.length > 0 && (
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Risk Factors</h3>
              <ul className="space-y-2">
                {result.risk_reasons.map((reason, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-orange-400 mt-0.5">⚠</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Recommendations</h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-blue-400 mt-0.5">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Info Box */}
      {!result && !loading && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-white font-semibold mb-3">How Ethereum Quantum Risk Works</h3>
          <div className="space-y-3 text-sm text-gray-400">
            <div className="flex items-start gap-3">
              <span className="text-purple-400 font-bold mt-0.5">1</span>
              <p><strong className="text-gray-300">Public Key Exposure:</strong> Every time you send a transaction from an Ethereum EOA, your public key becomes visible on-chain. A sufficiently powerful quantum computer could use Shor's algorithm to derive your private key from the exposed public key.</p>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-purple-400 font-bold mt-0.5">2</span>
              <p><strong className="text-gray-300">Transaction History:</strong> Addresses with outgoing transactions have already exposed their public key. Addresses that have only received ETH (no outgoing tx) are safer, as the public key hasn't been revealed yet.</p>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-purple-400 font-bold mt-0.5">3</span>
              <p><strong className="text-gray-300">Smart Contracts:</strong> Contract addresses are not directly vulnerable to quantum key attacks, but may be indirectly affected if their controlling EOA is compromised.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
