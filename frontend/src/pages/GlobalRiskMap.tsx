import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { LatLngExpression } from 'leaflet';

interface RiskMarker {
  lat: number;
  lng: number;
  risk: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  value: number;
  region: string;
}

export default function GlobalRiskMap() {
  const [markers, setMarkers] = useState<RiskMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [globalStats, setGlobalStats] = useState({ btc: 0, eth: 0 });

  useEffect(() => {
    fetchMapData();
  }, []);

  const fetchMapData = async () => {
    try {
      const response = await fetch('/api/intelligence/map', {
        headers: { 'X-API-Key': localStorage.getItem('apiKey') || 'demo_key' }
      });
      const data = await response.json();
      
      const convertedMarkers: RiskMarker[] = data.features.map((feature: any) => ({
        lat: feature.geometry.coordinates[1],
        lng: feature.geometry.coordinates[0],
        risk: feature.properties.risk,
        value: feature.properties.value,
        region: feature.properties.region || 'Unknown'
      }));
      
      setMarkers(convertedMarkers);
      setGlobalStats({ btc: 15000, eth: 8000 });
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch map data:', error);
      setLoading(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL': return '#ef4444';
      case 'HIGH': return '#f97316';
      case 'MEDIUM': return '#eab308';
      case 'LOW': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getRiskRadius = (value: number) => {
    return Math.sqrt(value) * 2;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading global risk map...</p>
        </div>
      </div>
    );
  }

  const mapCenter: LatLngExpression = [20, 0];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="w-8 h-8 text-blue-400" />
            <h1 className="text-3xl font-bold text-white">Global Quantum Risk Map</h1>
          </div>
          <p className="text-gray-400">Real-time visualization of quantum-vulnerable assets across Bitcoin and Ethereum networks</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Bitcoin at Risk</p>
                <p className="text-2xl font-bold text-white mt-2">{globalStats.btc.toLocaleString()} BTC</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500" />
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Ethereum at Risk</p>
                <p className="text-2xl font-bold text-white mt-2">{globalStats.eth.toLocaleString()} ETH</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden" style={{ height: '600px' }}>
          <MapContainer center={mapCenter} zoom={2} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            {markers.map((marker, idx) => (
              <CircleMarker
                key={idx}
                center={[marker.lat, marker.lng] as LatLngExpression}
                radius={getRiskRadius(marker.value)}
                pathOptions={{
                  fillColor: getRiskColor(marker.risk),
                  color: getRiskColor(marker.risk),
                  weight: 2,
                  opacity: 0.8,
                  fillOpacity: 0.6
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-bold">{marker.region}</p>
                    <p>Risk Level: <span className="font-bold text-red-500">{marker.risk}</span></p>
                    <p>Value at Risk: {marker.value.toLocaleString()} BTC/ETH</p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-gray-400 text-sm mb-3">Risk Level Legend</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { level: 'CRITICAL', color: '#ef4444' },
              { level: 'HIGH', color: '#f97316' },
              { level: 'MEDIUM', color: '#eab308' },
              { level: 'LOW', color: '#22c55e' }
            ].map(item => (
              <div key={item.level} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: item.color }}
                ></div>
                <span className="text-gray-300 text-sm">{item.level}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
