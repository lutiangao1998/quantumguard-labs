import { useState } from 'react';
import { Usb, HardDrive, CheckCircle, XCircle, Info, AlertTriangle } from 'lucide-react';

export default function HardwareWallet() {
  const [deviceType, setDeviceType] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<any>(null);
  const [txData, setTxData] = useState('');
  const [pqcAlgorithm, setPqcAlgorithm] = useState('ML-DSA-65');
  const [signingPayload, setSigningPayload] = useState<any>(null);
  const [signature, setSignature] = useState('');
  const [pubkey, setPubkey] = useState('');
  const [verificationResult, setVerificationResult] = useState<boolean | null>(null);

  const handleConnect = async () => {
    try {
      const response = await fetch('/api/hardware_wallet/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('apiKey') || 'demo_key'
        },
        body: JSON.stringify({ device_type: deviceType })
      });
      const data = await response.json();
      setConnectionStatus(data);
    } catch (error) {
      console.error('Connection error:', error);
      setConnectionStatus({ status: 'error', message: 'Failed to connect to device' });
    }
  };

  const handlePrepareSigning = async () => {
    try {
      const response = await fetch('/api/hardware_wallet/prepare_pqc_signing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('apiKey') || 'demo_key'
        },
        body: JSON.stringify({ tx_data: JSON.parse(txData), algorithm: pqcAlgorithm })
      });
      const data = await response.json();
      setSigningPayload(data.payload);
    } catch (error) {
      console.error('Prepare signing error:', error);
      setSigningPayload({ status: 'error', message: 'Failed to prepare signing payload' });
    }
  };

  const handleVerifySignature = async () => {
    try {
      const response = await fetch('/api/hardware_wallet/verify_pqc_signature', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('apiKey') || 'demo_key'
        },
        body: JSON.stringify({ signature, pubkey, algorithm: pqcAlgorithm })
      });
      const data = await response.json();
      setVerificationResult(data.is_valid);
    } catch (error) {
      console.error('Verification error:', error);
      setVerificationResult(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <HardDrive className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Hardware Wallet PQC Integration</h1>
          </div>
          <p className="text-gray-400">Integrate and manage your quantum-safe hardware wallets for secure asset migration.</p>
        </div>

        {/* Connection Section */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">1. Connect Device</h2>
          <div className="flex items-center gap-4 mb-4">
            <select
              className="flex-grow p-2 rounded-md bg-slate-700 text-white border border-slate-600 focus:ring-blue-500 focus:border-blue-500"
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
            >
              <option value="">Select Device</option>
              <option value="Ledger Nano S/X">Ledger Nano S/X</option>
              <option value="Trezor Model T">Trezor Model T</option>
            </select>
            <button
              onClick={handleConnect}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              disabled={!deviceType}
            >
              <Usb className="inline-block mr-2" size={18} /> Connect
            </button>
          </div>
          {connectionStatus && (
            <div className={`p-3 rounded-md ${connectionStatus.status === 'success' ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
              {connectionStatus.status === 'success' ? <CheckCircle className="inline-block mr-2" size={18} /> : <XCircle className="inline-block mr-2" size={18} />}
              {connectionStatus.message || `Connected to ${connectionStatus.device}. Firmware: ${connectionStatus.firmware_version}`}
            </div>
          )}
        </div>

        {/* PQC Signing Section */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">2. Prepare PQC Signing Payload</h2>
          <div className="mb-4">
            <label htmlFor="txData" className="block text-gray-400 text-sm font-bold mb-2">Transaction Data (JSON):</label>
            <textarea
              id="txData"
              className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600 focus:ring-blue-500 focus:border-blue-500"
              rows={5}
              value={txData}
              onChange={(e) => setTxData(e.target.value)}
              placeholder="e.g., { \"hash\": \"0x...\", \"amount\": 1.0 }"
            ></textarea>
          </div>
          <div className="flex items-center gap-4 mb-4">
            <select
              className="flex-grow p-2 rounded-md bg-slate-700 text-white border border-slate-600 focus:ring-blue-500 focus:border-blue-500"
              value={pqcAlgorithm}
              onChange={(e) => setPqcAlgorithm(e.target.value)}
            >
              <option value="ML-DSA-65">ML-DSA-65</option>
              <option value="Falcon-512">Falcon-512</option>
            </select>
            <button
              onClick={handlePrepareSigning}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
              disabled={!txData}
            >
              <Info className="inline-block mr-2" size={18} /> Prepare Payload
            </button>
          </div>
          {signingPayload && (
            <div className={`p-3 rounded-md ${signingPayload.status === 'error' ? 'bg-red-600/20 text-red-400' : 'bg-blue-600/20 text-blue-400'}`}>
              <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(signingPayload, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* Signature Verification Section */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4">3. Verify PQC Signature</h2>
          <div className="mb-4">
            <label htmlFor="signature" className="block text-gray-400 text-sm font-bold mb-2">Signature (Hex):</label>
            <input
              type="text"
              id="signature"
              className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600 focus:ring-blue-500 focus:border-blue-500"
              value={signature}
              onChange={(e) => setSignature(e.target.value)}
              placeholder="Enter PQC signature from hardware wallet"
            />
          </div>
          <div className="mb-4">
            <label htmlFor="pubkey" className="block text-gray-400 text-sm font-bold mb-2">Public Key (Hex):</label>
            <input
              type="text"
              id="pubkey"
              className="w-full p-2 rounded-md bg-slate-700 text-white border border-slate-600 focus:ring-blue-500 focus:border-blue-500"
              value={pubkey}
              onChange={(e) => setPubkey(e.target.value)}
              placeholder="Enter corresponding PQC public key"
            />
          </div>
          <button
            onClick={handleVerifySignature}
            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
            disabled={!signature || !pubkey}
          >
            <CheckCircle className="inline-block mr-2" size={18} /> Verify Signature
          </button>
          {verificationResult !== null && (
            <div className={`mt-4 p-3 rounded-md ${verificationResult ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
              {verificationResult ? <CheckCircle className="inline-block mr-2" size={18} /> : <AlertTriangle className="inline-block mr-2" size={18} />}
              Signature is {verificationResult ? 'VALID' : 'INVALID'}.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
