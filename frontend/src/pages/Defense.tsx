import { useState, useEffect } from 'react';
import { Shield, ArrowRightLeft, Heart, Globe, Activity, CheckCircle, AlertTriangle, Search, Lock, TrendingUp } from 'lucide-react';

export default function Defense() {
  const [activeTab, setActiveTab] = useState('bridge');
  const [bridgeData, setBridgeData] = useState({ source: 'BTC', target: 'PQC-Chain', address: '', amount: 0, asset: 'BTC' });
  const [bridgeStatus, setBridgeStatus] = useState<any>(null);
  const [insuranceData, setInsuranceData] = useState({ address: '', amount: 0, asset: 'BTC', riskScore: 0.5 });
  const [policy, setPolicy] = useState<any>(null);
  const [qnsDomain, setQnsDomain] = useState('');
  const [qnsResult, setQnsResult] = useState<any>(null);
  const [qDayPrediction, setQDayPrediction] = useState<any>(null);
  const [threatFeed, setThreatFeed] = useState<any[]>([]);

  useEffect(() => {
    if (activeTab === 'ai') {
      fetchQDayPrediction();
      fetchThreatFeed();
    }
  }, [activeTab]);

  const fetchQDayPrediction = async () => {
    try {
      const response = await fetch('/api/defense/ai/q_day_prediction', {
        headers: { 'X-API-Key': localStorage.getItem('apiKey') || 'demo_key' }
      });
      const data = await response.json();
      setQDayPrediction(data);
    } catch (error) {
      console.error('Fetch Q-Day prediction error:', error);
    }
  };

  const fetchThreatFeed = async () => {
    try {
      const response = await fetch('/api/defense/ai/threat_feed', {
        headers: { 'X-API-Key': localStorage.getItem('apiKey') || 'demo_key' }
      });
      const data = await response.json();
      setThreatFeed(data);
    } catch (error) {
      console.error('Fetch threat feed error:', error);
    }
  };

  const handleInitiateBridge = async () => {
    try {
      const response = await fetch('/api/defense/bridge/initiate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('apiKey') || 'demo_key'
        },
        body: JSON.stringify(bridgeData)
      });
      const data = await response.json();
      setBridgeStatus(data);
    } catch (error) {
      console.error('Initiate bridge error:', error);
    }
  };

  const handlePurchaseInsurance = async () => {
    try {
      const response = await fetch('/api/defense/insurance/purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('apiKey') || 'demo_key'
        },
        body: JSON.stringify(insuranceData)
      });
      const data = await response.json();
      setPolicy(data);
    } catch (error) {
      console.error('Purchase insurance error:', error);
    }
  };

  const handleResolveQNS = async () => {
    try {
      const response = await fetch(`/api/defense/qns/resolve/${qnsDomain}`, {
        headers: { 'X-API-Key': localStorage.getItem('apiKey') || 'demo_key' }
      });
      const data = await response.json();
      setQnsResult(data);
    } catch (error) {
      console.error('Resolve QNS error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-8 h-8 text-indigo-400" />
            <h1 className="text-3xl font-bold text-white">Full-Stack Quantum Defense</h1>
          </div>
          <p className="text-gray-400">Advanced ecosystem for cross-chain PQC bridging, quantum risk insurance, and AI-driven threat intelligence.</p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-700 mb-6 overflow-x-auto">
          {[
            { id: 'bridge', icon: ArrowRightLeft, label: 'PQC Bridge' },
            { id: 'insurance', icon: Heart, label: 'Quantum Insurance' },
            { id: 'qns', icon: Globe, label: 'PQC Name Service' },
            { id: 'ai', icon: Activity, label: 'AI Threat Predictor' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap ${
                activeTab === tab.id ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'bridge' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <ArrowRightLeft className="w-6 h-6 text-indigo-400" />
                <h2 className="text-xl font-semibold text-white">PQC Cross-Chain Bridge</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Source Chain:</label>
                  <select className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={bridgeData.source} onChange={(e) => setBridgeData({...bridgeData, source: e.target.value})}>
                    <option value="BTC">Bitcoin</option>
                    <option value="ETH">Ethereum</option>
                  </select>
                </div>
                <div className="flex items-center justify-center pt-6">
                  <ArrowRightLeft className="text-gray-500" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Target Chain (PQC):</label>
                  <select className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={bridgeData.target} onChange={(e) => setBridgeData({...bridgeData, target: e.target.value})}>
                    <option value="PQC-Chain">QuantumGuard PQC Chain</option>
                    <option value="ETH-L2-PQC">Ethereum L2 PQC</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-gray-400 text-sm font-bold mb-2">Source Address:</label>
                  <input type="text" className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={bridgeData.address} onChange={(e) => setBridgeData({...bridgeData, address: e.target.value})} placeholder="Enter source address" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Amount:</label>
                  <input type="number" className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={bridgeData.amount} onChange={(e) => setBridgeData({...bridgeData, amount: parseFloat(e.target.value)})} />
                </div>
              </div>
              <button onClick={handleInitiateBridge} className="w-full py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-bold">Initiate PQC Bridge Request</button>
              {bridgeStatus && (
                <div className="mt-6 p-4 bg-slate-900/50 rounded-lg border border-indigo-500/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-indigo-400 font-semibold">Bridge Status: {bridgeStatus.status}</span>
                    <span className="text-xs text-gray-500">ID: {bridgeStatus.tx_id}</span>
                  </div>
                  <p className="text-sm text-gray-300">Target PQC Address: <code className="text-indigo-300">{bridgeStatus.target_address}</code></p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-green-400">
                    <Lock size={14} /> PQC Signature Required (ML-DSA-65)
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'insurance' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Heart className="w-6 h-6 text-pink-400" />
                <h2 className="text-xl font-semibold text-white">Quantum Risk Insurance</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Asset Address:</label>
                  <input type="text" className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={insuranceData.address} onChange={(e) => setInsuranceData({...insuranceData, address: e.target.value})} placeholder="0x..." />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Coverage Amount:</label>
                  <input type="number" className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={insuranceData.amount} onChange={(e) => setInsuranceData({...insuranceData, amount: parseFloat(e.target.value)})} />
                </div>
              </div>
              <button onClick={handlePurchaseInsurance} className="w-full py-3 bg-pink-600 text-white rounded-md hover:bg-pink-700 font-bold">Purchase Quantum Insurance Policy</button>
              {policy && (
                <div className="mt-6 p-4 bg-slate-900/50 rounded-lg border border-pink-500/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-pink-400 font-semibold">Policy Status: {policy.status}</span>
                    <span className="text-xs text-gray-500">ID: {policy.policy_id}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p className="text-gray-400">Premium Paid:</p><p className="text-white">{policy.premium_paid.toFixed(4)} {policy.asset}</p>
                    <p className="text-gray-400">Expires At:</p><p className="text-white">{new Date(policy.expires_at).toLocaleDateString()}</p>
                  </div>
                  <div className="mt-2 flex items-center gap-2 text-xs text-green-400">
                    <CheckCircle size={14} /> PQC Certified Protection
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'qns' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Globe className="w-6 h-6 text-emerald-400" />
                <h2 className="text-xl font-semibold text-white">PQC Name Service (QNS)</h2>
              </div>
              <div className="mb-6">
                <label className="block text-gray-400 text-sm font-bold mb-2">Resolve Domain:</label>
                <div className="flex gap-2">
                  <input type="text" className="flex-grow p-2 rounded-md bg-slate-700 text-white border border-slate-600" value={qnsDomain} onChange={(e) => setQnsDomain(e.target.value)} placeholder="e.g. manus.pqc" />
                  <button onClick={handleResolveQNS} className="px-6 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 flex items-center gap-2"><Search size={18} /> Resolve</button>
                </div>
              </div>
              {qnsResult && (
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                  <h3 className="text-white font-semibold mb-2">{qnsResult.domain_name}</h3>
                  <p className="text-sm text-gray-400 mb-1">Resolved Address:</p>
                  <p className="text-emerald-400 font-mono break-all text-sm">{qnsResult.address}</p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-green-400">
                    <CheckCircle size={14} /> PQC Ownership Verified
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="space-y-6">
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <Activity className="w-6 h-6 text-orange-400" />
                    <h2 className="text-xl font-semibold text-white">AI-Quantum Threat Predictor</h2>
                  </div>
                  {qDayPrediction && (
                    <div className="px-3 py-1 bg-red-600/20 text-red-400 rounded-full text-xs font-bold border border-red-500/30">
                      Threat Level: {qDayPrediction.threat_level}
                    </div>
                  )}
                </div>
                {qDayPrediction && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 text-center">
                      <p className="text-gray-400 text-sm mb-1">Predicted Q-Day</p>
                      <p className="text-4xl font-bold text-white">{qDayPrediction.predicted_year}</p>
                      <p className="text-xs text-gray-500 mt-2">Window: {qDayPrediction.risk_window}</p>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 text-center">
                      <p className="text-gray-400 text-sm mb-1">Confidence Score</p>
                      <p className="text-4xl font-bold text-orange-400">{(qDayPrediction.confidence_score * 100).toFixed(1)}%</p>
                      <div className="w-full bg-slate-700 h-2 rounded-full mt-3">
                        <div className="bg-orange-500 h-2 rounded-full" style={{width: `${qDayPrediction.confidence_score * 100}%`}}></div>
                      </div>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700">
                      <p className="text-gray-400 text-sm mb-2">Key Risk Factors</p>
                      <ul className="text-xs text-gray-300 space-y-1">
                        {qDayPrediction.key_factors.map((f: string, i: number) => (
                          <li key={i} className="flex items-center gap-2"><TrendingUp size={12} className="text-red-400" /> {f}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h3 className="text-lg font-semibold text-white mb-4">Real-time Quantum Threat Feed</h3>
                <div className="space-y-4">
                  {threatFeed.map((item) => (
                    <div key={item.id} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700 flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold px-2 py-0.5 bg-slate-700 text-gray-300 rounded">{item.category}</span>
                          <span className="text-xs text-gray-500">{new Date(item.timestamp).toLocaleDateString()}</span>
                        </div>
                        <h4 className="text-white font-medium">{item.title}</h4>
                        <p className="text-xs text-gray-400 mt-1">Source: {item.source}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500 mb-1">Impact</p>
                        <span className={`text-sm font-bold ${item.impact_score > 0.8 ? 'text-red-400' : 'text-orange-400'}`}>
                          {(item.impact_score * 10).toFixed(1)}/10
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
