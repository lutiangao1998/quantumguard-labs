import { useState, useEffect } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { ShieldCheck, AlertTriangle, TrendingUp, Layers } from 'lucide-react'
import { analyzePortfolio, type AnalysisResponse } from '../api/client'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#f44336',
  HIGH:     '#ff9800',
  MEDIUM:   '#ffc107',
  LOW:      '#4caf50',
  SAFE:     '#2196f3',
}

function ScoreGauge({ score }: { score: number }) {
  const color = score < 40 ? '#f44336' : score < 60 ? '#ff9800' : score < 75 ? '#ffc107' : score < 90 ? '#4caf50' : '#2196f3'
  const label = score < 40 ? 'CRITICAL RISK' : score < 60 ? 'HIGH RISK' : score < 75 ? 'MODERATE' : score < 90 ? 'GOOD' : 'EXCELLENT'
  return (
    <div className="flex flex-col items-center justify-center p-6">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#1e293b" strokeWidth="12" />
          <circle
            cx="60" cy="60" r="50" fill="none"
            stroke={color} strokeWidth="12"
            strokeDasharray={`${(score / 100) * 314} 314`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{score.toFixed(0)}</span>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>
      </div>
      <div className="mt-2 text-sm font-semibold" style={{ color }}>{label}</div>
      <div className="text-xs text-slate-400 mt-1">Quantum Readiness Score</div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, sub, color }: any) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex items-center gap-4">
      <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: color + '20' }}>
        <Icon size={22} style={{ color }} />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-slate-400">{label}</div>
        {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState<AnalysisResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await analyzePortfolio({ utxo_count: 200 })
      setData(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const pieData = data ? [
    { name: 'CRITICAL', value: data.critical_count },
    { name: 'HIGH',     value: data.high_count },
    { name: 'MEDIUM',   value: data.medium_count },
    { name: 'LOW',      value: data.low_count },
    { name: 'SAFE',     value: data.safe_count },
  ].filter(d => d.value > 0) : []

  const barData = data ? [
    { name: 'CRITICAL', count: data.critical_count, btc: +data.critical_value_btc.toFixed(4) },
    { name: 'HIGH',     count: data.high_count,     btc: +data.high_value_btc.toFixed(4) },
    { name: 'MEDIUM',   count: data.medium_count,   btc: 0 },
    { name: 'LOW',      count: data.low_count,      btc: 0 },
    { name: 'SAFE',     count: data.safe_count,     btc: 0 },
  ] : []

  // Custom tooltip for pie chart
  const PieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const { name, value } = payload[0];
      const total = pieData.reduce((sum: number, item: any) => sum + item.value, 0);
      const percent = ((value / total) * 100).toFixed(1);
      return (
        <div className="bg-slate-900 border border-slate-700 rounded px-3 py-2 shadow-lg">
          <p className="text-xs font-semibold" style={{ color: RISK_COLORS[name] }}>
            {name}
          </p>
          <p className="text-xs text-slate-300">
            {value} UTXOs ({percent}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Risk Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Real-time quantum exposure overview for your Bitcoin portfolio</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
        >
          {loading ? 'Analyzing...' : 'Refresh Analysis'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-3 text-slate-400">Running quantum risk analysis...</span>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={Layers}       label="Total UTXOs"       value={data.total_utxos.toLocaleString()} sub={`${data.total_value_btc.toFixed(4)} BTC`} color="#1a73e8" />
            <StatCard icon={AlertTriangle} label="Critical + High"  value={data.critical_count + data.high_count} sub="Require immediate action" color="#f44336" />
            <StatCard icon={TrendingUp}    label="At-Risk BTC"      value={(data.critical_value_btc + data.high_value_btc).toFixed(4)} sub="BTC exposed to quantum risk" color="#ff9800" />
            <StatCard icon={ShieldCheck}   label="Safe UTXOs"       value={data.safe_count} sub="Already quantum-safe" color="#4caf50" />
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gauge + Pie */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-300 mb-4">Portfolio Risk Composition</h2>
              <div className="flex flex-col items-center gap-4">
                <ScoreGauge score={data.quantum_readiness_score} />
                <div className="w-full h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie 
                        data={pieData} 
                        dataKey="value" 
                        cx="50%" 
                        cy="50%" 
                        outerRadius={70}
                        label={false}
                      >
                        {pieData.map(entry => (
                          <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                        ))}
                      </Pie>
                      <Tooltip content={<PieTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                {/* Legend below pie chart */}
                <div className="w-full grid grid-cols-2 gap-2 text-xs">
                  {pieData.map(item => {
                    const total = pieData.reduce((sum: number, d: any) => sum + d.value, 0);
                    const percent = ((item.value / total) * 100).toFixed(1);
                    return (
                      <div key={item.name} className="flex items-center gap-2">
                        <div 
                          className="w-2 h-2 rounded-full" 
                          style={{ backgroundColor: RISK_COLORS[item.name] }}
                        />
                        <span className="text-slate-400">
                          {item.name.slice(0, 3)} {percent}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Bar chart */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-slate-300 mb-4">UTXO Count by Risk Level</h2>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Bar dataKey="count" name="UTXOs" radius={[4, 4, 0, 0]}>
                      {barData.map(entry => (
                        <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Top critical UTXOs */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-slate-300 mb-4">Top Priority UTXOs (Critical & High Risk)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 text-xs border-b border-slate-700">
                    <th className="text-left py-2 pr-4">TXID</th>
                    <th className="text-left py-2 pr-4">Address</th>
                    <th className="text-left py-2 pr-4">Script Type</th>
                    <th className="text-right py-2 pr-4">Value (BTC)</th>
                    <th className="text-left py-2">Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {data.assessments
                    .filter(a => a.risk_level === 'CRITICAL' || a.risk_level === 'HIGH')
                    .slice(0, 8)
                    .map((a, i) => (
                      <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                        <td className="py-2 pr-4 font-mono text-xs text-slate-300">{a.txid.slice(0, 16)}...</td>
                        <td className="py-2 pr-4 font-mono text-xs text-slate-300">{a.address.slice(0, 18)}...</td>
                        <td className="py-2 pr-4 text-slate-300">{a.script_type}</td>
                        <td className="py-2 pr-4 text-right text-slate-200">{a.value_btc.toFixed(6)}</td>
                        <td className="py-2">
                          <span
                            className="px-2 py-0.5 rounded text-xs font-semibold"
                            style={{ backgroundColor: RISK_COLORS[a.risk_level] + '30', color: RISK_COLORS[a.risk_level] }}
                          >
                            {a.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
