import { useState, useEffect } from 'react';
import { ShieldCheck, Lock, Globe, Smartphone, CheckCircle, AlertTriangle, FileText, Fingerprint, QrCode, Bell } from 'lucide-react';

export default function CompliancePrivacy() {
  const [activeTab, setActiveTab] = useState('zkp');
  const [zkpData, setZkpData] = useState({ source: '', target: '', amount: 0, secret: '' });
  const [complianceRegion, setComplianceRegion] = useState('EU');
  const [mobileAlerts, setMobileAlerts] = useState<any[]>([]);

  useEffect(() => {
    // 模拟获取移动端预警
    setMobileAlerts([
      { id: 'ALERT-001', type: 'WHALE_MOVEMENT', severity: 'HIGH', message: 'Large vulnerable asset movement detected on BTC network.', timestamp: '1 hour ago' },
      { id: 'ALERT-002', type: 'QUANTUM_THREAT_UPDATE', severity: 'MEDIUM', message: 'New research paper published on Shor\'s algorithm optimization.', timestamp: '2 hours ago' }
    ]);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShieldCheck className="text-indigo-400" /> Global Compliance & Privacy
        </h1>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-indigo-900/50 text-indigo-300 rounded-full text-xs border border-indigo-500/30 flex items-center gap-1">
            <Lock size={12} /> ZKP Enabled
          </span>
          <span className="px-3 py-1 bg-green-900/50 text-green-300 rounded-full text-xs border border-green-500/30 flex items-center gap-1">
            <Globe size={12} /> Multi-Region Support
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        <button 
          onClick={() => setActiveTab('zkp')}
          className={`px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'zkp' ? 'text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}
        >
          ZKP Privacy Migration
          {activeTab === 'zkp' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-400" />}
        </button>
        <button 
          onClick={() => setActiveTab('compliance')}
          className={`px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'compliance' ? 'text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Compliance Engine
          {activeTab === 'compliance' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-400" />}
        </button>
        <button 
          onClick={() => setActiveTab('coldstorage')}
          className={`px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'coldstorage' ? 'text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Q-Safe Cold Storage
          {activeTab === 'coldstorage' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-400" />}
        </button>
        <button 
          onClick={() => setActiveTab('mobile')}
          className={`px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'mobile' ? 'text-indigo-400' : 'text-gray-400 hover:text-gray-200'}`}
        >
          Mobile Guard
          {activeTab === 'mobile' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-400" />}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'zkp' && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Fingerprint className="text-indigo-400" /> ZKP Privacy Migration
              </h2>
              <p className="text-gray-400 text-sm mb-6">
                Generate a Zero-Knowledge Proof to migrate assets without revealing the source address on-chain.
              </p>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Source Address (Vulnerable)</label>
                    <input 
                      type="text" 
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                      placeholder="0x... or 1..."
                      value={zkpData.source}
                      onChange={(e) => setZkpData({...zkpData, source: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Target PQC Address</label>
                    <input 
                      type="text" 
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                      placeholder="pqc1..."
                      value={zkpData.target}
                      onChange={(e) => setZkpData({...zkpData, target: e.target.value})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Amount</label>
                    <input 
                      type="number" 
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                      placeholder="0.00"
                      value={zkpData.amount}
                      onChange={(e) => setZkpData({...zkpData, amount: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase">Secret Nullifier</label>
                    <input 
                      type="password" 
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                      placeholder="Keep this secret"
                      value={zkpData.secret}
                      onChange={(e) => setZkpData({...zkpData, secret: e.target.value})}
                    />
                  </div>
                </div>
                <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
                  Generate ZKP Proof & Migrate
                </button>
              </div>
            </div>
          )}

          {activeTab === 'compliance' && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Globe className="text-indigo-400" /> Global Compliance Engine
              </h2>
              <div className="grid grid-cols-4 gap-4 mb-6">
                {['EU', 'US', 'HK', 'SG'].map(region => (
                  <button 
                    key={region}
                    onClick={() => setComplianceRegion(region)}
                    className={`py-3 rounded-lg border transition-all ${complianceRegion === region ? 'bg-indigo-900/30 border-indigo-500 text-white' : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'}`}
                  >
                    <div className="text-sm font-bold">{region}</div>
                    <div className="text-[10px] opacity-60">{region === 'EU' ? 'MiCA' : region === 'US' ? 'SOC2' : region === 'HK' ? 'VASP' : 'MAS'}</div>
                  </button>
                ))}
              </div>
              <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-4 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-300">Compliance Standard:</span>
                  <span className="text-sm font-mono text-indigo-400">{complianceRegion === 'EU' ? 'MiCA (Markets in Crypto-Assets)' : complianceRegion === 'US' ? 'SOC2 Type II' : complianceRegion === 'HK' ? 'VASP Licensing' : 'MAS Payment Services Act'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-300">PQC Audit Requirement:</span>
                  <span className="text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded border border-green-500/20">MANDATORY</span>
                </div>
                <button className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
                  <FileText size={18} /> Generate {complianceRegion} Compliance Report
                </button>
              </div>
            </div>
          )}

          {activeTab === 'coldstorage' && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <QrCode className="text-indigo-400" /> Q-Safe Cold Storage
              </h2>
              <div className="flex flex-col items-center justify-center py-8 border-2 border-dashed border-gray-800 rounded-xl bg-gray-800/20">
                <QrCode size={120} className="text-gray-600 mb-4" />
                <p className="text-gray-400 text-sm">Scan this QR code with your offline PQC signing device</p>
                <button className="mt-6 px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors">
                  Prepare Signing Payload
                </button>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                  <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">Protocol Version</h3>
                  <p className="text-sm text-white font-mono">QG-PQC-COLD-v1.0</p>
                </div>
                <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                  <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">Security Level</h3>
                  <p className="text-sm text-green-400 font-mono">AIR-GAPPED</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'mobile' && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Smartphone className="text-indigo-400" /> Mobile Guard
              </h2>
              <div className="space-y-4">
                {mobileAlerts.map(alert => (
                  <div key={alert.id} className="p-4 bg-gray-800/50 rounded-lg border border-gray-700 flex gap-4">
                    <div className={`p-2 rounded-full h-fit ${alert.severity === 'HIGH' ? 'bg-red-900/30 text-red-400' : 'bg-yellow-900/30 text-yellow-400'}`}>
                      <Bell size={18} />
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <h3 className="text-sm font-bold text-white">{alert.type}</h3>
                        <span className="text-[10px] text-gray-500">{alert.timestamp}</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{alert.message}</p>
                    </div>
                  </div>
                ))}
                <div className="pt-4 border-t border-gray-800">
                  <div className="flex items-center justify-between p-4 bg-indigo-900/20 rounded-lg border border-indigo-500/30">
                    <div className="flex items-center gap-3">
                      <Smartphone className="text-indigo-400" />
                      <div>
                        <p className="text-sm font-bold text-white">Register New Device</p>
                        <p className="text-[10px] text-indigo-300">Get real-time PQC alerts on your phone</p>
                      </div>
                    </div>
                    <button className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-medium transition-colors">
                      Register
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-wider">Security Status</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-900/30 text-green-400 rounded-lg">
                  <CheckCircle size={18} />
                </div>
                <div>
                  <p className="text-xs font-bold text-white">ZKP Engine</p>
                  <p className="text-[10px] text-gray-500">Operational - BN128</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-900/30 text-green-400 rounded-lg">
                  <CheckCircle size={18} />
                </div>
                <div>
                  <p className="text-xs font-bold text-white">Compliance Rules</p>
                  <p className="text-[10px] text-gray-500">Updated 2026-03-05</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-900/30 text-yellow-400 rounded-lg">
                  <AlertTriangle size={18} />
                </div>
                <div>
                  <p className="text-xs font-bold text-white">Mobile Sync</p>
                  <p className="text-[10px] text-gray-500">2 devices active</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-xl p-6">
            <h3 className="text-sm font-bold text-indigo-300 mb-2">Pro Tip</h3>
            <p className="text-xs text-indigo-200/70 leading-relaxed">
              Use ZKP Privacy Migration to prevent chain-analysis tools from linking your old vulnerable address to your new PQC-safe identity.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
