import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AnalysisRequest {
  utxo_count?: number
  use_testnet?: boolean
  testnet_address?: string
}

export interface UTXOResult {
  txid: string
  vout: number
  address: string
  value_btc: number
  script_type: string
  risk_level: string
  risk_score: number
  migration_priority: number
  risk_reasons: string[]
}

export interface AnalysisResponse {
  total_utxos: number
  total_value_btc: number
  quantum_readiness_score: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  safe_count: number
  critical_value_btc: number
  high_value_btc: number
  assessments: UTXOResult[]
}

export interface MigrationRequest {
  utxo_count?: number
  policy?: 'emergency' | 'standard' | 'dry_run'
  destination_address?: string
}

export interface BatchSummary {
  batch_id: string
  batch_number: number
  utxo_count: number
  total_value_btc: number
  status: string
  risk_levels: string[]
}

export interface MigrationPlanResponse {
  plan_id: string
  policy_name: string
  total_batches: number
  total_utxos: number
  total_value_btc: number
  estimated_fees_btc: number
  batches: BatchSummary[]
}

export interface BlockchainStatusResponse {
  network: string
  connector_type: string
  status: string
  block_height?: number
  api_url?: string
}

// ── API Calls ─────────────────────────────────────────────────────────────────

export const analyzePortfolio = (req: AnalysisRequest = {}) =>
  api.post<AnalysisResponse>('/analysis/run', req).then(r => r.data)

export const createMigrationPlan = (req: MigrationRequest = {}) =>
  api.post<MigrationPlanResponse>('/migration/plan', req).then(r => r.data)

export const getMigrationPolicies = () =>
  api.get('/migration/policies').then(r => r.data)

export const downloadPdfReport = async (utxo_count = 100, org_id = 'DEMO_ORG') => {
  const resp = await api.get('/reports/pdf', {
    params: { utxo_count, org_id },
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([resp.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `quantumguard_report_${Date.now()}.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}

export const getJsonReport = (utxo_count = 100, org_id = 'DEMO_ORG') =>
  api.get('/reports/json', { params: { utxo_count, org_id } }).then(r => r.data)

export const getBlockchainStatus = () =>
  api.get<BlockchainStatusResponse>('/blockchain/status').then(r => r.data)

export const scanTestnetAddress = (address: string) =>
  api.get('/blockchain/scan', { params: { address } }).then(r => r.data)


export default api
