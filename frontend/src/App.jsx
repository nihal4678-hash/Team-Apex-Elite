import { useState, useEffect } from 'react'
import {
  Activity, ArrowUpRight, Bell, Building2, Check, ChevronDown, CircleHelp,
  CloudSun, Eye, EyeOff, Gauge, Leaf, LockKeyhole, LogOut, Menu, Play,
  Search, Settings, SlidersHorizontal, Sparkles, ThermometerSun, TrendingDown, X
} from 'lucide-react'
import {
  getCampusSnapshot, getBuildings, getForecast, getAlerts,
  getRecommendations, applyRecommendation, resolveAlert, runSimulation,
  getSustainability, getGeminiCostExplanation, getGeminiAnomalySummary,
  getGeminiApprovalSupport, getGeminiScenarioAnalysis, getGeminiExecutiveReport,
  askGeminiQuestion
} from './services/api'
import { SimulationPage } from './pages/SimulationPage'
import { ForecastPage } from './pages/ForecastPage'
import { AlertsPage } from './pages/AlertsPage'
import './App.css'

const navItems = [
  { label: 'Overview', icon: Gauge },
  { label: 'Buildings', icon: Building2 },
  { label: 'Forecast', icon: TrendingDown },
  { label: 'Alerts', icon: Bell, badge: '3' },
  { label: 'Sustainability', icon: Leaf },
  { label: 'Simulation', icon: SlidersHorizontal },
]

function App() {
  const [signedIn, setSignedIn] = useState(false)
  const [activePage, setActivePage] = useState('Overview')
  const [showApproval, setShowApproval] = useState(false)
  const [approved, setApproved] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  // Live State
  const [snapshot, setSnapshot] = useState({})
  const [buildings, setBuildings] = useState([])
  const [forecastBars, setForecastBars] = useState([52, 61, 57, 66, 72, 69, 78, 74, 83, 79, 88, 84, 91, 86, 94, 90, 82, 76, 69, 62, 56, 49, 45, 42])
  const [alerts, setAlerts] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [sustainabilityData, setSustainabilityData] = useState(null)
  const [simResult, setSimResult] = useState(null)

  // Gemini Intelligence State
  const [costExplanation, setCostExplanation] = useState(null)
  const [anomalySummary, setAnomalySummary] = useState(null)
  const [approvalSupport, setApprovalSupport] = useState(null)
  const [scenarioData, setScenarioData] = useState(null)
  const [executiveReport, setExecutiveReport] = useState(null)
  const [userQuery, setUserQuery] = useState('')
  const [qaResult, setQaResult] = useState(null)
  const [isAsking, setIsAsking] = useState(false)
  const [activeScenarioFilter, setActiveScenarioFilter] = useState(null)

  const loadData = async () => {
    const snap = await getCampusSnapshot()
    if (snap) setSnapshot(snap)

    const bList = await getBuildings()
    if (bList) setBuildings(bList)

    const fc = await getForecast()
    if (fc && fc.actual && fc.forecast) {
      setForecastBars([...fc.actual, ...fc.forecast])
    }

    const al = await getAlerts()
    if (al) setAlerts(al)

    const recs = await getRecommendations()
    if (recs) setRecommendations(recs)

    const sus = await getSustainability()
    if (sus) setSustainabilityData(sus)

    // Load Gemini Intelligence Contexts
    const costExp = await getGeminiCostExplanation()
    if (costExp) setCostExplanation(costExp)

    const anomSum = await getGeminiAnomalySummary()
    if (anomSum) setAnomalySummary(anomSum)

    const scData = await getGeminiScenarioAnalysis()
    if (scData) setScenarioData(scData)

    const execRep = await getGeminiExecutiveReport()
    if (execRep) setExecutiveReport(execRep)
  }

  useEffect(() => {
    if (signedIn) {
      loadData()
    }
  }, [signedIn])

  const selectPage = (page) => { setActivePage(page); setMenuOpen(false) }

  // Closed-loop action handler with Gemini feedback
  const handleApproveAction = async () => {
    const topRec = recommendations[0]
    const recId = topRec ? topRec.recommendation_id : 'REC-HVAC-001'
    await applyRecommendation(recId)
    setApproved(true)
    setShowApproval(false)
    await loadData()
  }

  const handleOpenApprovalModal = async () => {
    setShowApproval(true)
    const topRec = recommendations[0]
    const recId = topRec ? topRec.recommendation_id : 'REC-HVAC-001'
    const supp = await getGeminiApprovalSupport(recId)
    if (supp) setApprovalSupport(supp)
  }

  const handleResolveAlert = async (alertId) => {
    await resolveAlert(alertId)
    await loadData()
  }

  const handleTriggerSim = async (bId) => {
    const res = await runSimulation(bId, -2, 60)
    setSimResult(res)
  }

  const handleAskQuestion = async (e) => {
    e.preventDefault()
    if (!userQuery.trim()) return
    setIsAsking(true)
    const ans = await askGeminiQuestion(userQuery)
    setQaResult(ans)
    setIsAsking(false)
  }

  if (!signedIn) return <LoginPage onLogin={() => setSignedIn(true)} />

  return (
    <main className="app-shell">
      <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`}>
        <div className="brand">
          <span className="brand-mark"><Leaf size={17} /></span>
          <span>ecomind<span className="brand-dot">.</span></span>
        </div>
        <div className="workspace-switcher">
          <span className="workspace-icon">VU</span>
          <span><strong>Vignan University</strong><small>Vadlamudi Campus</small></span>
          <ChevronDown size={14} />
        </div>
        <nav className="main-nav" aria-label="Main navigation">
          <p className="nav-label">Workspace</p>
          {navItems.map(({ label, icon: Icon, badge }) => (
            <button
              className={`nav-item ${activePage === label ? 'active' : ''}`}
              key={label}
              onClick={() => selectPage(label)}
            >
              <Icon size={18} />
              <span>{label}</span>
              {badge && <b>{badge}</b>}
            </button>
          ))}
          <p className="nav-label nav-label-spaced">Account</p>
          <button className="nav-item" onClick={() => selectPage('Settings')}>
            <Settings size={18} />
            <span>Settings</span>
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="help-link"><CircleHelp size={17} /><span>Help center</span></div>
          <div className="user-chip">
            <span className="avatar">JD</span>
            <span><strong>Jordan Davis</strong><small>Energy manager</small></span>
            <button className="sign-out" onClick={() => setSignedIn(false)} aria-label="Sign out" title="Sign out">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      <section className="content-area">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <div>
            <p className="eyebrow">Gemini AI Intelligence Layer Active · VFSTR Campus</p>
            <h1>{activePage === 'Overview' ? 'Good morning, Jordan' : activePage}</h1>
          </div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Notifications"><Bell size={19} /><i /></button>
            <div className="top-avatar">JD</div>
          </div>
        </header>

        {activePage === 'Overview' && (
          <div className="status-strip">
            <span className="status-dot" />
            <strong>Gemini Intelligence & Closed-Loop Engine Active</strong>
            <span className="status-separator" />
            <span>ML Computations + Gemini Natural Language Reasoning</span>
            <button onClick={loadData}>Refresh AI Insights <ArrowUpRight size={14} /></button>
          </div>
        )}

        {/* Natural Language Q&A Bar */}
        {activePage === 'Overview' && (
          <div style={{ margin: '0 0 1.25rem 0', padding: '1rem', background: '#fff', borderRadius: '12px', border: '1px solid var(--color-border)', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
            <form onSubmit={handleAskQuestion} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <Sparkles size={20} style={{ color: '#16a34a' }} />
              <input
                type="text"
                value={userQuery}
                onChange={(e) => setUserQuery(e.target.value)}
                placeholder="Ask Gemini AI (e.g. 'Which building wasted the most energy?' or 'How much can we save?')"
                style={{ flex: 1, padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.92rem' }}
              />
              <button type="submit" className="button-primary" disabled={isAsking} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Search size={15} /> {isAsking ? 'Reasoning...' : 'Ask Gemini'}
              </button>
            </form>

            {qaResult && (
              <div style={{ marginTop: '1rem', padding: '0.85rem 1rem', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                <strong style={{ color: '#15803d', display: 'block', marginBottom: '0.25rem' }}>Gemini Response:</strong>
                <p style={{ margin: 0, color: '#166534', fontSize: '0.94rem' }}>{qaResult.answer}</p>
                {qaResult.cited_metrics && (
                  <small style={{ color: '#15803d', marginTop: '0.4rem', display: 'block' }}>
                    Cited Sources: {qaResult.cited_metrics.join(', ')}
                  </small>
                )}
              </div>
            )}
          </div>
        )}

        {activePage === 'Overview' ? (
          <div className="content-grid">
            <section className="hero-panel">
              <div className="hero-copy">
                <span className="section-kicker">ENERGY SNAPSHOT <Activity size={14} /></span>
                <h2>Campus energy is<br /><em>trending efficiently.</em></h2>
                <p>Consumption is down {snapshot.weekly_change_percent || -12.4}% compared to baseline.</p>
                <div className="hero-metric">
                  <strong>{snapshot.energy_used_today_kwh || 847}</strong>
                  <span>kWh<br /><small>used today</small></span>
                </div>
              </div>
              <div className="hero-chart">
                <div className="chart-topline">
                  <span>Today's load profile (ML Forecast & Telemetry)</span>
                  <span className="chart-legend"><i /> Actual <i className="forecast-dot" /> Forecast</span>
                </div>
                <div className="bar-chart">
                  {forecastBars.map((height, index) => (
                    <div className={`bar ${index > 15 ? 'forecast' : ''}`} key={index} style={{ '--bar-height': `${Math.min(100, height)}%` }} />
                  ))}
                </div>
                <div className="chart-axis">
                  <span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>Now</span>
                </div>
              </div>
            </section>

            <div className="kpi-grid">
              <KpiCard label="Monthly Savings (INR)" value={`₹${(snapshot.money_saved_month_inr || 55536).toLocaleString()}`} change="8.2%" detail="vs baseline" positive icon={<Activity size={18} />} />
              <KpiCard label="Carbon avoided" value={`${snapshot.carbon_avoided_kg || 426} kg`} change="14.6%" detail="vs last week" positive icon={<Leaf size={18} />} />
              <KpiCard label="Peak demand" value={`${snapshot.peak_demand_kw || 186} kW`} change="5.1%" detail="vs last week" icon={<ThermometerSun size={18} />} />
            </div>

            {/* Gemini Executive Insights Card */}
            <section className="panel insight-panel" style={{ gridColumn: 'span 12', background: 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%)', borderColor: '#bbf7d0' }}>
              <div className="insight-heading">
                <span className="spark-icon" style={{ background: '#dcfce7', color: '#16a34a' }}><Sparkles size={18} /></span>
                <div>
                  <span className="section-kicker" style={{ color: '#15803d' }}>GEMINI AI EXECUTIVE REASONING</span>
                  <h3 style={{ color: '#14532d' }}>{costExplanation ? `Next-Month Forecast: ₹${costExplanation.predicted_cost_inr?.toLocaleString()}` : 'Campus Energy Executive Summary'}</h3>
                </div>
              </div>
              <p style={{ color: '#166534', fontSize: '0.95rem', lineHeight: '1.5' }}>
                {costExplanation?.cost_trend_explanation || executiveReport?.executive_summary || 'Gemini AI is analyzing real-time campus telemetry and forecasting trends.'}
              </p>
            </section>

            <section className="panel buildings-panel">
              <PanelHeading title="Building performance (Vignan Campus)" action="View all buildings" onClickAction={() => selectPage('Buildings')} />
              <div className="building-list">
                {(buildings.length > 0 ? buildings.slice(0, 4) : []).map((b, idx) => (
                  <BuildingRow key={idx} name={b.name || b.id} type={`${b.category || 'academic'} · ${b.kw} kW`} value={`${b.kw} kW`} percent={`${b.load}%`} color={b.load > 80 ? 'amber' : 'lime'} />
                ))}
              </div>
            </section>

            <section className="panel insight-panel">
              <div className="insight-heading">
                <span className="spark-icon"><Sparkles size={17} /></span>
                <div>
                  <span className="section-kicker">RECOMMENDED CONTROL ACTION</span>
                  <h3>{recommendations[0]?.title || 'Pre-cool labs before peak heat'}</h3>
                </div>
              </div>
              <p>{recommendations[0]?.description || 'Adjust AC setpoints in Academic Block A & CSE Labs during 15:30 peak load window.'}</p>
              <div className="insight-footer">
                <span><CloudSun size={16} /> Est savings: ₹{recommendations[0]?.money_saved_inr || 4805}</span>
                <button onClick={handleOpenApprovalModal} className={approved ? 'approved' : ''}>
                  {approved ? <><Check size={15} /> Approved & Applied</> : <><Play size={14} /> Review & Apply</>}
                </button>
              </div>
            </section>

            <section className="panel alerts-panel">
              <PanelHeading title="Recent ML Anomalies" action="See all alerts" onClickAction={() => selectPage('Alerts')} />
              {(alerts.length > 0 ? alerts.slice(0, 3) : []).map((al, idx) => (
                <div className="alert-row" key={idx}>
                  <span className={`alert-icon ${al.severity === 'critical' ? 'amber' : 'green'}`}><ThermometerSun size={16} /></span>
                  <span><strong>{al.type}</strong><small>{al.building} · {al.message}</small></span>
                  <button className={`severity ${al.status === 'resolved' ? 'resolved' : ''}`} onClick={() => handleResolveAlert(al.id)}>
                    {al.status === 'resolved' ? 'Resolved' : 'Resolve'}
                  </button>
                </div>
              ))}
            </section>
          </div>
        ) : activePage === 'Buildings' ? (
          <BuildingsView buildings={buildings} onSim={handleTriggerSim} simResult={simResult} />
        ) : activePage === 'Forecast' ? (
          <ForecastPage />
        ) : activePage === 'Alerts' ? (
          <AlertsPage onResolveAlert={handleResolveAlert} initialScenarioId={activeScenarioFilter} />
        ) : activePage === 'Sustainability' ? (
          <SustainabilityView data={sustainabilityData} executiveReport={executiveReport} />
        ) : activePage === 'Simulation' ? (
          <SimulationPage buildings={buildings} onNavigateToAlerts={(scId) => { setActiveScenarioFilter(scId); setActivePage('Alerts'); }} />
        ) : (
          <PlaceholderPage page={activePage} onBack={() => selectPage('Overview')} />
        )}
      </section>

      {/* Gemini Approval Support Modal */}
      {showApproval && (
        <div className="modal-backdrop" onClick={() => setShowApproval(false)}>
          <div className="approval-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '540px' }}>
            <button className="modal-close" onClick={() => setShowApproval(false)} aria-label="Close"><X size={18} /></button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span className="modal-icon" style={{ background: '#dcfce7', color: '#16a34a' }}><Sparkles size={20} /></span>
              <span className="section-kicker" style={{ color: '#15803d', margin: 0 }}>GEMINI APPROVAL ADVISOR</span>
            </div>

            <h2>{recommendations[0]?.title || 'Approve Optimization Action?'}</h2>
            <p>{recommendations[0]?.description || 'EcoMind will adjust Academic Block HVAC setpoints to 26°C and stage fans.'}</p>

            {approvalSupport && (
              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', margin: '1rem 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>AI Verdict</span>
                  <span style={{ background: '#22c55e', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 700 }}>
                    {approvalSupport.verdict}
                  </span>
                </div>
                <p style={{ fontSize: '0.88rem', color: '#334155', margin: '0 0 0.5rem 0' }}>{approvalSupport.reasoning}</p>
                <small style={{ color: '#64748b' }}>Disruption Risk: <strong>{approvalSupport.operational_disruption_risk}</strong> · {approvalSupport.risk_notes}</small>
              </div>
            )}

            <div className="modal-impact">
              <span>Estimated financial impact</span>
              <strong>₹{recommendations[0]?.money_saved_inr || '4,805.61'}</strong>
            </div>

            <div className="modal-actions">
              <button className="button-secondary" onClick={() => setShowApproval(false)}>Not now</button>
              <button className="button-primary" onClick={handleApproveAction}>
                <Check size={16} /> Approve & Execute Loop
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

function KpiCard({ label, value, change, detail, positive, icon }) {
  return (
    <article className="kpi-card">
      <div className="kpi-head"><span>{label}</span><span className="kpi-icon">{icon}</span></div>
      <strong className="kpi-value">{value}</strong>
      <div className="kpi-change">
        <span className={positive ? 'positive' : 'negative'}>{positive ? '↓' : '↑'} {change}</span>
        <span>{detail}</span>
      </div>
    </article>
  )
}

function BuildingRow({ name, type, value, percent, color }) {
  return (
    <div className="building-row">
      <span className={`building-avatar ${color}`}><Building2 size={18} /></span>
      <span className="building-name"><strong>{name}</strong><small>{type}</small></span>
      <span className="load-track"><i style={{ width: percent }} /></span>
      <span className="building-value"><strong>{value}</strong><small>{percent} load</small></span>
    </div>
  )
}

function PanelHeading({ title, action, onClickAction }) {
  return (
    <div className="panel-heading">
      <h3>{title}</h3>
      <button onClick={onClickAction}>{action} <ArrowUpRight size={14} /></button>
    </div>
  )
}

function BuildingsView({ buildings, onSim, simResult }) {
  return (
    <div className="content-grid">
      <section className="panel" style={{ gridColumn: 'span 12' }}>
        <h3>Vignan University Campus Buildings</h3>
        <p style={{ marginBottom: '1rem', color: 'var(--color-muted)' }}>Real-time building load profiles driven by Phase 1 IoT digital twin telemetry.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {buildings.map((b, i) => (
            <div key={i} style={{ background: 'var(--color-bg)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
              <h4>{b.name}</h4>
              <p><small>Category: {b.category || 'Academic'}</small></p>
              <p>Current Load: <strong>{b.kw} kW</strong> ({b.load}% capacity)</p>
              <button className="button-secondary" style={{ marginTop: '0.5rem', width: '100%' }} onClick={() => onSim(b.id)}>
                Run Closed-Loop Simulation
              </button>
            </div>
          ))}
        </div>
        {simResult && (
          <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#eefdf5', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
            <span className="section-kicker">SIMULATION RESULT</span>
            <p>Building {simResult.building_id}: Pre-cooling by 2°C for 60 min saves <strong>{simResult.saved_kwh} kWh</strong> (₹{simResult.estimated_savings_inr})!</p>
          </div>
        )}
      </section>
    </div>
  )
}

function ForecastView({ forecastBars, costExplanation, scenarioData }) {
  return (
    <div className="content-grid">
      <section className="panel" style={{ gridColumn: 'span 12' }}>
        <h3>ML Load Forecast Engine (LightGBM/RandomForest)</h3>
        <p style={{ marginBottom: '1rem', color: 'var(--color-muted)' }}>Continuous 24-hour demand predictions vs actual smart meter readings.</p>
        <div className="bar-chart" style={{ height: '220px' }}>
          {forecastBars.map((h, idx) => (
            <div className={`bar ${idx > 15 ? 'forecast' : ''}`} key={idx} style={{ '--bar-height': `${Math.min(100, h)}%` }} />
          ))}
        </div>
      </section>

      {/* Gemini Cost Forecast Explanation Card */}
      {costExplanation && (
        <section className="panel" style={{ gridColumn: 'span 12', background: '#f8fafc' }}>
          <span className="section-kicker" style={{ color: '#15803d' }}>GEMINI NEXT-MONTH COST EXPLAINER</span>
          <h3>{costExplanation.target_month} Energy Cost Explanation</h3>
          <p style={{ marginTop: '0.5rem', fontSize: '0.94rem', color: '#334155' }}>{costExplanation.cost_trend_explanation}</p>
          
          <h4 style={{ marginTop: '1rem' }}>Top Cost Drivers:</h4>
          <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem' }}>
            {costExplanation.top_drivers?.map((d, i) => (
              <li key={i} style={{ fontSize: '0.9rem', margin: '0.25rem 0' }}>
                <strong>{d.driver} (+{d.impact_percent}%):</strong> {d.description}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Scenario Comparison Cards */}
      {scenarioData && (
        <section className="panel" style={{ gridColumn: 'span 12' }}>
          <h3>Gemini Scenario Comparison</h3>
          <p style={{ marginBottom: '1rem', color: 'var(--color-muted)' }}>{scenarioData.narrative_comparison}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div style={{ background: '#f0fdf4', padding: '1rem', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
              <span className="section-kicker" style={{ color: '#16a34a' }}>OPTIMISTIC (WITH ECOMIND SETBACK)</span>
              <strong style={{ fontSize: '1.4rem', display: 'block', margin: '0.25rem 0', color: '#15803d' }}>₹{scenarioData.optimistic_cost_inr?.toLocaleString()}</strong>
              <small style={{ color: '#166534' }}>Full closed-loop setback & pre-cooling active (-12.4% cost)</small>
            </div>

            <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <span className="section-kicker" style={{ color: '#475569' }}>BASELINE OPERATIONS</span>
              <strong style={{ fontSize: '1.4rem', display: 'block', margin: '0.25rem 0', color: '#334155' }}>₹{scenarioData.baseline_cost_inr?.toLocaleString()}</strong>
              <small style={{ color: '#64748b' }}>Current unoptimized campus operation baseline</small>
            </div>

            <div style={{ background: '#fff7ed', padding: '1rem', borderRadius: '8px', border: '1px solid #fed7aa' }}>
              <span className="section-kicker" style={{ color: '#c2410c' }}>PESSIMISTIC (HEATWAVE SURGE)</span>
              <strong style={{ fontSize: '1.4rem', display: 'block', margin: '0.25rem 0', color: '#9a3412' }}>₹{scenarioData.pessimistic_cost_inr?.toLocaleString()}</strong>
              <small style={{ color: '#9a3412' }}>High temperature spike (+12.5% demand increase)</small>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

function AlertsView({ alerts, anomalySummary, onResolve }) {
  return (
    <div className="content-grid">
      {/* Gemini Human-Readable Waste Summary */}
      {anomalySummary && (
        <section className="panel" style={{ gridColumn: 'span 12', background: '#fff7ed', borderColor: '#ffedd5' }}>
          <span className="section-kicker" style={{ color: '#c2410c' }}>GEMINI OPERATIONAL WASTE SUMMARY</span>
          <h3 style={{ color: '#9a3412' }}>{anomalySummary.total_anomalies_count} Total Anomalies ({anomalySummary.critical_count} Critical)</h3>
          <p style={{ marginTop: '0.5rem', color: '#7c2d12', fontSize: '0.94rem' }}>{anomalySummary.operational_advice}</p>
        </section>
      )}

      <section className="panel" style={{ gridColumn: 'span 12' }}>
        <h3>ML Anomaly & Leak Detection Log</h3>
        <div className="building-list" style={{ marginTop: '1rem' }}>
          {alerts.map((al, idx) => (
            <div className="alert-row" key={idx} style={{ padding: '0.75rem 0' }}>
              <span className={`alert-icon ${al.severity === 'critical' ? 'amber' : 'green'}`}><ThermometerSun size={16} /></span>
              <span><strong>{al.type} ({al.building})</strong><small>{al.message} — Action: {al.recommended_action}</small></span>
              <button className={`severity ${al.status === 'resolved' ? 'resolved' : ''}`} onClick={() => onResolve(al.id)}>
                {al.status === 'resolved' ? 'Resolved' : 'Resolve'}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

function SustainabilityView({ data, executiveReport }) {
  return (
    <div className="content-grid">
      {/* Gemini Executive Report */}
      {executiveReport && (
        <section className="panel" style={{ gridColumn: 'span 12', background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <span className="section-kicker" style={{ color: '#15803d' }}>DEAN-READY EXECUTIVE SUSTAINABILITY REPORT</span>
          <h3 style={{ color: '#14532d' }}>{executiveReport.campus_name}</h3>
          <p style={{ marginTop: '0.5rem', color: '#166534', fontSize: '0.95rem' }}>{executiveReport.executive_summary}</p>
          
          <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <h4 style={{ color: '#15803d' }}>Top Inefficiencies Identified:</h4>
              <ul style={{ paddingLeft: '1.2rem', margin: '0.4rem 0' }}>
                {executiveReport.top_inefficiencies?.map((ineff, i) => (
                  <li key={i} style={{ fontSize: '0.88rem', color: '#166534' }}>{ineff}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 style={{ color: '#15803d' }}>Strategic Action Priorities:</h4>
              <ul style={{ paddingLeft: '1.2rem', margin: '0.4rem 0' }}>
                {executiveReport.strategic_action_plan?.map((act, i) => (
                  <li key={i} style={{ fontSize: '0.88rem', color: '#166534' }}>{act}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      <section className="panel" style={{ gridColumn: 'span 12' }}>
        <h3>ESG & Sustainability Leaderboard</h3>
        <p style={{ marginBottom: '1rem', color: 'var(--color-muted)' }}>
          Grid Carbon Factor: 0.82 kg CO₂/kWh · Tariff: ₹8.75/kWh (AP Commercial Tariff)
        </p>
        {data?.green_leaderboard && (
          <div className="building-list">
            {data.green_leaderboard.map((lb, i) => (
              <div key={i} className="building-row">
                <span><strong>#{lb.leaderboard_rank} {lb.building_name}</strong></span>
                <span>Efficiency Score: <strong>{Math.round(lb.efficiency_score)}%</strong></span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function PlaceholderPage({ page, onBack }) {
  return (
    <div className="placeholder">
      <div className="placeholder-icon"><Settings size={22} /></div>
      <span className="section-kicker">ECOMIND WORKSPACE</span>
      <h2>{page} is connected to the backend closed-loop API.</h2>
      <button className="button-primary" onClick={onBack}>Back to overview <ArrowUpRight size={15} /></button>
    </div>
  )
}

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!email || !password) { setError('Enter your email and password to continue.'); return }
    setError('')
    onLogin()
  }

  return (
    <main className="login-shell">
      <div className="login-visual">
        <div className="login-brand">
          <span className="brand-mark"><Leaf size={17} /></span>
          <span>ecomind<span className="brand-dot">.</span></span>
        </div>
        <div className="visual-copy">
          <span className="section-kicker">VIGNAN UNIVERSITY ENERGY INTELLIGENCE</span>
          <h1>Make every<br /><em>watt matter.</em></h1>
          <p>Closed-loop ML optimization, Gemini natural-language reasoning, digital twin telemetry, and real-time operations.</p>
        </div>
        <div className="visual-foot">
          <span><Activity size={15} /> Live energy operations</span>
          <span>Vadlamudi Campus · 2026</span>
        </div>
      </div>
      <section className="login-form-wrap">
        <div className="login-form-card">
          <span className="section-kicker">WELCOME BACK</span>
          <h2>Sign in to your workspace</h2>
          <p className="login-subtitle">Vignan University Energy Hub</p>
          <form onSubmit={handleSubmit}>
            <label>
              Email address
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="jordan@vignan.ac.in" autoComplete="email" />
            </label>
            <label>
              Password
              <span className="password-input">
                <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" />
                <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </span>
            </label>
            {error && <p className="login-error" role="alert">{error}</p>}
            <button className="login-submit" type="submit"><LockKeyhole size={16} /> Sign in</button>
          </form>
        </div>
      </section>
    </main>
  )
}

export default App
