import { useState } from 'react';
import { Users, Code, Zap, Bell, CheckCircle, XCircle, Info, AlertTriangle, Send } from 'lucide-react';

export default function Ecosystem() {
  const [activeTab, setActiveTab] = useState('multisig');
  const [multisigAddress, setMultisigAddress] = useState('');
  const [multisigBlockchain, setMultisigBlockchain] = useState('BTC');
  const [multisigInfo, setMultisigInfo] = useState<any>(null);
  const [contractAddress, setContractAddress] = useState('');
  const [contractInfo, setContractInfo] = useState<any>(null);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookEvents, setWebhookEvents] = useState<string[]>([]);
  const [webhookStatus, setWebhookStatus] = useState<any>(null);

  const handleParseMultisig = async () => {
    try {
      const response = await fetch(`/api/ecosystem/multisig/parse?address=${multisigAddress}&blockchain=${multisigBlockchain}`, {
        method: 'POST',
        headers: { 'X-API-Key': localStorage.getItem('apiKey') || 'demo_key' }
      });
      const data = await response.json();
      setMultisigInfo(data);
    } catch (error) {
      console.error('Parse multisig error:', error);
    }
  };

  const handleAnalyzeContract = async () => {
    try {
      const response = await fetch(`/api/ecosystem/contract/analyze?contract_address=${contractAddress}`, {
        method: 'POST',
        headers: { 'X-API-Key': localStorage.getItem('apiKey') || 'demo_key' }
      });
      const data = await response.json();
      setContractInfo(data);
    } catch (error) {
      console.error('Analyze contract error:', error);
    }
  };

  const handleSubscribeWebhook = async () => {
    try {
      const response = await fetch('/api/ecosystem/webhooks/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('apiKey') || 'demo_key'
        },
        body: JSON.stringify({ webhook_url: webhookUrl, event_types: webhookEvents })
      });
      const data = await response.json();
      setWebhookStatus(data);
    } catch (error) {
      console.error('Subscribe webhook error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-8 h-8 text-yellow-400" />
            <h1 className="text-3xl font-bold text-white">Ecosystem & Automation</h1>
          </div>
          <p className="text-gray-400">Institutional-grade tools for multisig migration, smart contract ownership, and automated risk response.</p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-700 mb-6">
          {['multisig', 'contract', 'automation', 'webhooks'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'multisig' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Users className="w-6 h-6 text-blue-400" />
                <h2 className="text-xl font-semibold text-white">Multisig & TSS Migration</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Blockchain:</label>
                  <select
                    className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600"
                    value={multisigBlockchain}
                    onChange={(e) => setMultisigBlockchain(e.target.value)}
                  >
                    <option value="BTC">Bitcoin</option>
                    <option value="ETH">Ethereum</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Multisig Address:</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      className="flex-grow p-2 rounded-md bg-slate-700 text-white border border-slate-600"
                      value={multisigAddress}
                      onChange={(e) => setMultisigAddress(e.target.value)}
                      placeholder="Enter multisig address"
                    />
                    <button onClick={handleParseMultisig} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Parse</button>
                  </div>
                </div>
              </div>
              {multisigInfo && (
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                  <h3 className="text-white font-semibold mb-3">Multisig Details</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><p className="text-gray-400">Type:</p><p className="text-white">{multisigInfo.type}</p></div>
                    <div><p className="text-gray-400">Threshold:</p><p className="text-white">{multisigInfo.threshold}</p></div>
                    <div className="col-span-2">
                      <p className="text-gray-400 mb-1">Participants/Owners:</p>
                      <ul className="list-disc list-inside text-white">
                        {(multisigInfo.participants || multisigInfo.owners).map((p: string, i: number) => (
                          <li key={i} className="truncate">{p}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="col-span-2">
                      <div className={`mt-2 p-2 rounded text-center font-bold ${multisigInfo.risk_level === 'CRITICAL' ? 'bg-red-600/20 text-red-400' : 'bg-orange-600/20 text-orange-400'}`}>
                        Risk Level: {multisigInfo.risk_level}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'contract' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Code className="w-6 h-6 text-green-400" />
                <h2 className="text-xl font-semibold text-white">Smart Contract Ownership Migration</h2>
              </div>
              <div className="mb-6">
                <label className="block text-gray-400 text-sm font-bold mb-2">Contract Address (Ethereum):</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    className="flex-grow p-2 rounded-md bg-slate-700 text-white border border-slate-600"
                    value={contractAddress}
                    onChange={(e) => setContractAddress(e.target.value)}
                    placeholder="0x..."
                  />
                  <button onClick={handleAnalyzeContract} className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">Analyze</button>
                </div>
              </div>
              {contractInfo && (
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                  <h3 className="text-white font-semibold mb-3">Contract Ownership Analysis</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><p className="text-gray-400">Pattern:</p><p className="text-white">{contractInfo.ownership_pattern}</p></div>
                    <div><p className="text-gray-400">Current Owner:</p><p className="text-white truncate">{contractInfo.current_owner}</p></div>
                    <div className="col-span-2">
                      <div className={`mt-2 p-2 rounded text-center font-bold ${contractInfo.risk_level === 'CRITICAL' ? 'bg-red-600/20 text-red-400' : 'bg-orange-600/20 text-orange-400'}`}>
                        Risk Level: {contractInfo.risk_level}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'automation' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Zap className="w-6 h-6 text-yellow-400" />
                <h2 className="text-xl font-semibold text-white">Auto-Migration Trigger</h2>
              </div>
              <div className="p-8 text-center border-2 border-dashed border-slate-700 rounded-lg">
                <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                <h3 className="text-white font-semibold mb-2">Automation Policy Builder</h3>
                <p className="text-gray-400 mb-6">Configure rules to automatically trigger asset migration based on quantum threat levels or whale activity.</p>
                <button className="px-6 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700">Create New Policy</button>
              </div>
            </div>
          )}

          {activeTab === 'webhooks' && (
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <div className="flex items-center gap-3 mb-6">
                <Bell className="w-6 h-6 text-purple-400" />
                <h2 className="text-xl font-semibold text-white">Webhooks & B2B Integration</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Webhook URL:</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    placeholder="https://your-api.com/webhook"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm font-bold mb-2">Event Types:</label>
                  <div className="grid grid-cols-2 gap-2">
                    {['WHALE_ALERT_TRIGGERED', 'QUANTUM_THREAT_LEVEL_INCREASED', 'MIGRATION_COMPLETED'].map(event => (
                      <label key={event} className="flex items-center gap-2 text-gray-300 text-sm">
                        <input
                          type="checkbox"
                          checked={webhookEvents.includes(event)}
                          onChange={(e) => {
                            if (e.target.checked) setWebhookEvents([...webhookEvents, event]);
                            else setWebhookEvents(webhookEvents.filter(ev => ev !== event));
                          }}
                        />
                        {event}
                      </label>
                    ))}
                  </div>
                </div>
                <button onClick={handleSubscribeWebhook} className="w-full py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 flex items-center justify-center gap-2">
                  <Send size={18} /> Subscribe Webhook
                </button>
                {webhookStatus && (
                  <div className="mt-4 p-3 bg-green-600/20 text-green-400 rounded-md flex items-center gap-2">
                    <CheckCircle size={18} /> Subscription Active: {webhookStatus.id}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
