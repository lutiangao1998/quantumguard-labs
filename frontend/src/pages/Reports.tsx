import { useState } from 'react'
import { downloadPdfReport, getJsonReport } from '../api/client'
import {
  FileText, Download, CheckCircle, Shield, BarChart3,
  ClipboardList, Lock, Award, TrendingUp, AlertCircle,
  Loader2, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react'

const REPORT_FEATURES = [
  { icon: BarChart3,     title: 'Executive Summary',       desc: 'Board-ready overview of quantum risk posture and migration progress.',          color: 'text-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/20' },
  { icon: Shield,        title: 'Risk Distribution Table', desc: 'Detailed breakdown of UTXOs by risk level with BTC values and exposure.',       color: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/20' },
  { icon: ClipboardList, title: 'Migration Plan Summary',  desc: 'Batch-by-batch migration schedule with status tracking and priority ordering.', color: 'text-amber-400',  bg: 'bg-amber-500/10',  border: 'border-amber-500/20' },
  { icon: Lock,          title: 'Audit Trail Integrity',   desc: 'Hash-chained tamper-evident log of all migration activities for forensics.',    color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  { icon: Award,         title: 'Formal Attestation',      desc: 'Regulatory-ready attestation statement for compliance submissions.',            color: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20' },
  { icon: TrendingUp,    title: 'Quantum Readiness Score', desc: 'Before/after score comparison with projected improvement trajectory.',          color: 'text-cyan-400',   bg: 'bg-cyan-500/10',   border: 'border-cyan-500/20' },
]

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? 'text-green-400' : score >= 50 ? 'text-amber-400' : 'text-red-400'
  const ring  = score >= 80 ? 'ring-green-500/40' : score >= 50 ? 'ring-amber-500/40' : 'ring-red-500/40'
  return (
    <div className={`flex flex-col items-center justify-center w-20 h-20 rounded-full ring-4 ${ring} bg-slate-900`}>
      <span className={`text-2xl font-bold ${color}`}>{score}</span>
      <span className="text-[10px] text-slate-500 uppercase tracking-wider">Score</span>
    </div>
  )
}

function RiskBar({ label, count, total, value, color }: { label: string; count: number; total: number; value: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <span className={`text-xs font-medium w-16 ${color}`}>{label}</span>
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color.replace('text-', 'bg-')}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{count}</span>
      <span className="text-xs text-slate-500 w-20 text-right">{value.toFixed(4)} BTC</span>
    </div>
  )
}

export default function Reports() {
  const [utxoCount, setUtxoCount] = useState(100)
  const [orgId, setOrgId] = useState('DEMO_ORG')
  const [loading, setLoading] = useState<'pdf' | 'json' | null>(null)
  const [jsonData, setJsonData] = useState<any>(null)
  const [jsonExpanded, setJsonExpanded] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handlePdf = async () => {
    setLoading('pdf'); setError(null)
    try { await downloadPdfReport(utxoCount, orgId) }
    catch (e: any) { setError(e?.message || 'Failed to generate PDF') }
    finally { setLoading(null) }
  }
  const handleJson = async () => {
    setLoading('json'); setError(null)
    try { const d = await getJsonReport(utxoCount, orgId); setJsonData(d); setJsonExpanded(true) }
    catch (e: any) { setError(e?.message || 'Failed to load JSON') }
    finally { setLoading(null) }
  }
  const report = jsonData?.report
  const summary = report?.executive_summary
  const dist = report?.risk_distribution
  const total = summary?.total_utxos ?? 0

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Compliance Reports</h1>
          <p className="text-slate-400 text-sm mt-1">Generate professional PDF and JSON compliance reports for auditors and regulators</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg">
          <CheckCircle size={14} className="text-green-400" />
          <span className="text-xs text-green-400 font-medium">NIST PQC Compliant</span>
        </div>
      </div>

      <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-slate-200 mb-4">Report Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Organization ID</label>
            <input value={orgId} onChange={e => setOrgId(e.target.value)} placeholder="e.g. ACME_CORP"
              className="w-full bg-slate-700/60 border border-slate-600 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">UTXO Sample Size</label>
            <input type="number" min={10} max={500} value={utxoCount} onChange={e => setUtxoCount(+e.target.value)}
              className="w-full bg-slate-700/60 border border-slate-600 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
          </div>
          <div className="flex flex-col justify-end">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2"><Shield size={11} /><span>Reports signed with ML-DSA-65</span></div>
            <div className="h-px bg-slate-700 rounded" />
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={handlePdf} disabled={!!loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors">
            {loading === 'pdf' ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            {loading === 'pdf' ? 'Generating...' : 'Download PDF Report'}
          </button>
          <button onClick={handleJson} disabled={!!loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors border border-slate-600">
            {loading === 'json' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {loading === 'json' ? 'Loading...' : 'View JSON Report'}
          </button>
        </div>
        {error && (
          <div className="mt-4 flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
            <AlertCircle size={14} />{error}
          </div>
        )}
      </div>

      {jsonData && (
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl overflow-hidden">
          {summary && (
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-sm font-semibold text-slate-200">Report Preview</h2>
                <span className="text-xs text-slate-500">{report?.metadata?.generated_at ? new Date(report.metadata.generated_at * 1000).toLocaleString() : ''}</span>
              </div>
              <div className="flex items-center gap-6 mb-6">
                <ScoreBadge score={Math.round(summary.quantum_readiness_score ?? 0)} />
                <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Total UTXOs', value: summary.total_utxos, color: 'text-white' },
                    { label: 'Total Value',  value: `${(summary.total_value_btc ?? 0).toFixed(4)} BTC`, color: 'text-amber-400' },
                    { label: 'Critical',     value: summary.critical_count, color: 'text-red-400' },
                    { label: 'High Risk',    value: summary.high_count, color: 'text-orange-400' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-slate-900/60 rounded-xl p-3">
                      <div className="text-xs text-slate-500 mb-1">{label}</div>
                      <div className={`text-lg font-bold ${color}`}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>
              {dist && (
                <div className="space-y-2.5">
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-3">Risk Distribution</div>
                  <RiskBar label="CRITICAL" count={dist.critical?.count ?? 0} total={total} value={dist.critical?.value_btc ?? 0} color="text-red-400" />
                  <RiskBar label="HIGH"     count={dist.high?.count ?? 0}     total={total} value={dist.high?.value_btc ?? 0}     color="text-orange-400" />
                  <RiskBar label="MEDIUM"   count={dist.medium?.count ?? 0}   total={total} value={dist.medium?.value_btc ?? 0}   color="text-amber-400" />
                  <RiskBar label="LOW"      count={dist.low?.count ?? 0}      total={total} value={dist.low?.value_btc ?? 0}      color="text-blue-400" />
                  <RiskBar label="SAFE"     count={dist.safe?.count ?? 0}     total={total} value={dist.safe?.value_btc ?? 0}     color="text-green-400" />
                </div>
              )}
            </div>
          )}
          <button onClick={() => setJsonExpanded(v => !v)}
            className="w-full flex items-center justify-between px-6 py-4 text-sm text-slate-400 hover:text-slate-300 hover:bg-slate-700/30 transition-colors">
            <span className="flex items-center gap-2"><ExternalLink size={13} />Raw JSON Data</span>
            {jsonExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {jsonExpanded && (
            <div className="px-6 pb-6">
              <pre className="text-xs text-slate-300 overflow-auto max-h-80 bg-slate-900/80 rounded-xl p-4 border border-slate-700">
                {JSON.stringify(jsonData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">What's Included in Every Report</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {REPORT_FEATURES.map(({ icon: Icon, title, desc, color, bg, border }) => (
            <div key={title} className={`${bg} border ${border} rounded-2xl p-5`}>
              <div className="flex items-center gap-3 mb-3">
                <div className={`p-2 rounded-lg ${bg} border ${border}`}><Icon size={16} className={color} /></div>
                <span className="text-sm font-semibold text-white">{title}</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
