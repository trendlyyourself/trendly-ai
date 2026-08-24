import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { apiRequest } from '../lib/api'

type Connection = { connected: boolean; shop_domain?: string }
type Recommendation = { type: string; priority: string; reason: string; current: string | null; proposed: string | null; requires_approval: boolean }
type Product = { id: string; title: string; score: number; issues: string[]; inventory: number; status: string; recommendations: Recommendation[] }
type Scan = { shop_domain: string; product_count: number; issue_count: number; average_score: number; products: Product[] }

export default function ShopifyPage() {
  const { token, workspace } = useAuth()
  const [connection, setConnection] = useState<Connection>({ connected: false })
  const [shopDomain, setShopDomain] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [scan, setScan] = useState<Scan | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const headers = { Authorization: `Bearer ${token}` }

  const loadConnection = async () => {
    if (!workspace || !token) return
    try {
      const data = await apiRequest(`/shopify/connection?workspace_id=${workspace.id}`, { headers }) as Connection
      setConnection(data)
      if (data.shop_domain) setShopDomain(data.shop_domain)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load Shopify connection')
    }
  }

  useEffect(() => { void loadConnection() }, [workspace?.id, token])

  const connect = async () => {
    if (!workspace || !token) return
    setBusy(true); setError('')
    try {
      const data = await apiRequest('/shopify/connection', {
        method: 'POST', headers,
        body: JSON.stringify({ workspace_id: workspace.id, shop_domain: shopDomain, access_token: accessToken }),
      }) as Connection
      setConnection(data)
      setAccessToken('')
    } catch (err) { setError(err instanceof Error ? err.message : 'Connection failed') }
    finally { setBusy(false) }
  }

  const runScan = async () => {
    if (!workspace || !token) return
    setBusy(true); setError('')
    try {
      setScan(await apiRequest(`/shopify/scan?workspace_id=${workspace.id}`, { method: 'POST', headers }) as Scan)
    } catch (err) { setError(err instanceof Error ? err.message : 'Scan failed') }
    finally { setBusy(false) }
  }

  const disconnect = async () => {
    if (!workspace || !token) return
    setBusy(true); setError('')
    try {
      await apiRequest(`/shopify/connection?workspace_id=${workspace.id}`, { method: 'DELETE', headers })
      setConnection({ connected: false }); setScan(null); setShopDomain('')
    } catch (err) { setError(err instanceof Error ? err.message : 'Disconnect failed') }
    finally { setBusy(false) }
  }

  return <div className="grid">
    <div className="card">
      <h2>Shopify</h2>
      <p className="muted">Connect a real Shopify store and audit its live product catalog.</p>
      {!connection.connected ? <div className="stack" style={{ marginTop: '1rem' }}>
        <label className="field"><span>Shopify store domain</span><input value={shopDomain} onChange={e => setShopDomain(e.target.value)} /></label>
        <label className="field"><span>Admin API access token</span><input type="password" value={accessToken} onChange={e => setAccessToken(e.target.value)} autoComplete="off" /></label>
        <button className="button" disabled={busy || !shopDomain || !accessToken} onClick={() => void connect()}>{busy ? 'Connecting…' : 'Connect store'}</button>
      </div> : <div className="stack" style={{ marginTop: '1rem' }}>
        <div className="workspace-row"><div><div className="workspace-name">{connection.shop_domain}</div><div className="workspace-slug">Connected to live Shopify Admin API</div></div><button className="button button-secondary" style={{ width: 'auto' }} disabled={busy} onClick={() => void disconnect()}>Disconnect</button></div>
        <button className="button" disabled={busy} onClick={() => void runScan()}>{busy ? 'Scanning catalog…' : 'Run SEO audit'}</button>
      </div>}
      {error && <div className="error-box">{error}</div>}
    </div>

    {scan && <>
      <div className="stats-grid">
        <div className="stat-card"><div className="stat-label">Products scanned</div><div className="stat-value">{scan.product_count}</div></div>
        <div className="stat-card"><div className="stat-label">Issues found</div><div className="stat-value">{scan.issue_count}</div></div>
        <div className="stat-card"><div className="stat-label">Average SEO health</div><div className="stat-value">{scan.average_score}/100</div></div>
      </div>
      <div className="card"><h2>Product audit</h2><div className="workspace-list" style={{ marginTop: '1rem' }}>
        {scan.products.map(product => <div className="workspace-row" key={product.id}>
          <div style={{ minWidth: 0 }}>
            <div className="workspace-name">{product.title}</div>
            <div className="workspace-slug">{product.issues.length ? product.issues.join(' · ') : 'No detected issues'}</div>
            {product.recommendations.length > 0 && <div className="stack" style={{ marginTop: '0.75rem' }}>
              {product.recommendations.map((recommendation, index) => <div className="card" key={`${recommendation.type}-${index}`} style={{ padding: '0.9rem' }}>
                <strong>{recommendation.type.replaceAll('_', ' ')}</strong>
                <div className="workspace-slug">{recommendation.reason}</div>
                {recommendation.proposed && <div style={{ marginTop: '0.5rem' }}><span className="muted">Recommended:</span> {recommendation.proposed}</div>}
                <div className="muted" style={{ marginTop: '0.4rem' }}>Requires merchant approval before any Shopify change.</div>
              </div>)}
            </div>}
          </div>
          <strong>{product.score}/100</strong>
        </div>)}
      </div></div>
    </>}
  </div>
}
