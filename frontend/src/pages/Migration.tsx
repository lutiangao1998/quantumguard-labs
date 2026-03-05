import { useState } from 'react'
import { createMigrationPlan, type MigrationPlanResponse } from '../api/client'
import { CheckCircle, Clock, AlertCircle } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  DRY_RUN_COMPLETE: '#2196f3',
  PENDING_APPROVAL: '#ff9800',
  APPROVED:         '#4caf50',
  EXECUTING:        '#00bcd4',
  COMPLETED:        '#4caf50',
  FAILED:           '#f44336',
}

export default function Migration() {
  const [utxoCount, setUtxoCount] = useState(200)
  const [policy, setPolicy] = useState<'emergency' | 'standard' | 'dry_run'>('dry_run')
  const [destAddr, setDestAddr] = useState('bc1p_quantum_safe_destination_address')
  const [plan, setPlan] = useState<MigrationPlanResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const res = await createMigrationPlan({
        utxo_count: utxoCount,
        policy,
        destination_address: destAddr,
      })
      setPlan(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Migration Planner</h1>
        <p className="text-slate-400 text-sm mt-1">Generate a policy-driven, batched migration plan for at-risk UTXOs</p>
      </div>

      {/* Config */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">Migration Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">UTXO Count</label>
            <input
              type="number" min={10} max={500} value={utxoCount}
              onChange={e => setUtxoCount(+e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Migration Policy</label>
            <select
              value={policy} onChange={e => setPolicy(e.target.value as any)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="dry_run">Dry Run (Simulation)</option>
              <option value="standard">Standard (Delayed Execution)</option>
              <option value="emergency">Emergency (Immediate)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Destination Address</label>
            <input
              value={destAddr} onChange={e => setDestAddr(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono"
            />
          </div>
        </div>

        {/* Policy descriptions */}
        <div className="grid grid-cols-3 gap-3 mt-2">
          {[
            { key: 'dry_run',   icon: AlertCircle, color: '#2196f3', title: 'Dry Run', desc: 'Simulate migration without broadcasting. Safe for testing.' },
            { key: 'standard',  icon: Clock,       color: '#ff9800', title: 'Standard', desc: '24h delay, multi-sig approval required. Recommended for production.' },
            { key: 'emergency', icon: CheckCircle, color: '#f44336', title: 'Emergency', desc: 'Immediate execution for critical risk UTXOs only.' },
          ].map(({ key, icon: Icon, color, title, desc }) => (
            <div
              key={key}
              onClick={() => setPolicy(key as any)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                policy === key ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-500'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon size={14} style={{ color }} />
                <span className="text-sm font-semibold text-white">{title}</span>
              </div>
              <p className="text-xs text-slate-400">{desc}</p>
            </div>
          ))}
        </div>

        <button
          onClick={generate} disabled={loading}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
        >
          {loading ? 'Generating Plan...' : 'Generate Migration Plan'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-3 text-slate-400">Building migration plan...</span>
        </div>
      )}

      {plan && !loading && (
        <>
          {/* Plan summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Batches',   value: plan.total_batches },
              { label: 'UTXOs to Migrate', value: plan.total_utxos },
              { label: 'Total Value',     value: `${plan.total_value_btc.toFixed(4)} BTC` },
              { label: 'Est. Fees',       value: `${plan.estimated_fees_btc.toFixed(6)} BTC` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
                <div className="text-xl font-bold text-white">{value}</div>
                <div className="text-xs text-slate-400 mt-1">{label}</div>
              </div>
            ))}
          </div>

          {/* Plan ID */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle size={18} className="text-green-400 shrink-0" />
            <div>
              <div className="text-sm font-semibold text-white">Migration Plan Generated</div>
              <div className="text-xs text-slate-400 font-mono mt-0.5">Plan ID: {plan.plan_id}</div>
              <div className="text-xs text-slate-400">Policy: <span className="text-cyan-400">{plan.policy_name}</span></div>
            </div>
          </div>

          {/* Batch list */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h2 className="text-sm font-semibold text-slate-300">Migration Batches</h2>
            </div>
            <div className="divide-y divide-slate-700/50">
              {plan.batches.map(batch => (
                <div key={batch.batch_id} className="px-5 py-4 flex items-center gap-4 hover:bg-slate-700/30 transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center text-sm font-bold text-white shrink-0">
                    {batch.batch_number}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-mono text-slate-300 truncate">{batch.batch_id.slice(0, 24)}...</div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {batch.utxo_count} UTXOs · {batch.total_value_btc.toFixed(4)} BTC ·
                      Risk: {batch.risk_levels.join(', ')}
                    </div>
                  </div>
                  <span
                    className="px-2.5 py-1 rounded text-xs font-semibold shrink-0"
                    style={{
                      backgroundColor: (STATUS_COLORS[batch.status] ?? '#888') + '25',
                      color: STATUS_COLORS[batch.status] ?? '#888',
                    }}
                  >
                    {batch.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
