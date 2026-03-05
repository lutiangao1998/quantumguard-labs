import { useState } from 'react'
import { downloadPdfReport, getJsonReport } from '../api/client'
import { FileText, Download, CheckCircle } from 'lucide-react'

export default function Reports() {
  const [utxoCount, setUtxoCount] = useState(100)
  const [orgId, setOrgId] = useState('DEMO_ORG')
  const [loading, setLoading] = useState<'pdf' | 'json' | null>(null)
  const [jsonData, setJsonData] = useState<any>(null)

  const handlePdf = async () => {
    setLoading('pdf')
    try { await downloadPdfReport(utxoCount, orgId) }
    catch (e) { console.error(e) }
    finally { setLoading(null) }
  }

  const handleJson = async () => {
    setLoading('json')
    try {
      const data = await getJsonReport(utxoCount, orgId)
      setJsonData(data)
    } catch (e) { console.error(e) }
    finally { setLoading(null) }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Compliance Reports</h1>
        <p className="text-slate-400 text-sm mt-1">Generate professional PDF and JSON compliance reports for auditors and regulators</p>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">Report Configuration</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Organization ID</label>
            <input
              value={orgId} onChange={e => setOrgId(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">UTXO Sample Size</label>
            <input
              type="number" min={10} max={500} value={utxoCount}
              onChange={e => setUtxoCount(+e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
            />
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handlePdf} disabled={!!loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
          >
            <FileText size={14} />
            {loading === 'pdf' ? 'Generating PDF...' : 'Download PDF Report'}
          </button>
          <button
            onClick={handleJson} disabled={!!loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
          >
            <Download size={14} />
            {loading === 'json' ? 'Loading...' : 'View JSON Report'}
          </button>
        </div>
      </div>

      {/* Report features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { title: 'Executive Summary', desc: 'Board-ready overview of quantum risk posture and migration progress.' },
          { title: 'Risk Distribution Table', desc: 'Detailed breakdown of UTXOs by risk level with BTC values.' },
          { title: 'Migration Plan Summary', desc: 'Batch-by-batch migration schedule with status tracking.' },
          { title: 'Audit Trail Integrity', desc: 'Hash-chained tamper-evident log of all migration activities.' },
          { title: 'Formal Attestation', desc: 'Regulatory-ready attestation statement for compliance submissions.' },
          { title: 'Quantum Readiness Score', desc: 'Before/after score comparison with projected improvement.' },
        ].map(({ title, desc }) => (
          <div key={title} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle size={14} className="text-green-400" />
              <span className="text-sm font-semibold text-white">{title}</span>
            </div>
            <p className="text-xs text-slate-400">{desc}</p>
          </div>
        ))}
      </div>

      {jsonData && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">JSON Report Preview</h2>
          <pre className="text-xs text-slate-300 overflow-auto max-h-96 bg-slate-900 rounded-lg p-4">
            {JSON.stringify(jsonData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
