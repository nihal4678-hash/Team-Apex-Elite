import { useState } from 'react'
import { Activity, ArrowUpRight, Bell, Building2, Check, ChevronDown, CircleHelp, CloudSun, Eye, EyeOff, Gauge, Leaf, LockKeyhole, LogOut, Menu, MoreHorizontal, Play, Settings, SlidersHorizontal, Sparkles, ThermometerSun, TrendingDown, X } from 'lucide-react'
import './App.css'

const navItems = [
  { label: 'Overview', icon: Gauge }, { label: 'Buildings', icon: Building2 }, { label: 'Forecast', icon: TrendingDown },
  { label: 'Alerts', icon: Bell, badge: '3' }, { label: 'Sustainability', icon: Leaf }, { label: 'Simulation', icon: SlidersHorizontal },
]
const bars = [52, 61, 57, 66, 72, 69, 78, 74, 83, 79, 88, 84, 91, 86, 94, 90, 82, 76, 69, 62, 56, 49, 45, 42]

function App() {
  const [signedIn, setSignedIn] = useState(false)
  const [activePage, setActivePage] = useState('Overview')
  const [showApproval, setShowApproval] = useState(false)
  const [approved, setApproved] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const selectPage = (page) => { setActivePage(page); setMenuOpen(false) }
  if (!signedIn) return <LoginPage onLogin={() => setSignedIn(true)} />

  return <main className="app-shell">
    <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`}>
      <div className="brand"><span className="brand-mark"><Leaf size={17} /></span><span>ecomind<span className="brand-dot">.</span></span></div>
      <div className="workspace-switcher"><span className="workspace-icon">NC</span><span><strong>North Campus</strong><small>Energy operations</small></span><ChevronDown size={14} /></div>
      <nav className="main-nav" aria-label="Main navigation"><p className="nav-label">Workspace</p>{navItems.map(({ label, icon: Icon, badge }) => <button className={`nav-item ${activePage === label ? 'active' : ''}`} key={label} onClick={() => selectPage(label)}><Icon size={18} /><span>{label}</span>{badge && <b>{badge}</b>}</button>)}<p className="nav-label nav-label-spaced">Account</p><button className="nav-item" onClick={() => selectPage('Settings')}><Settings size={18} /><span>Settings</span></button></nav>
      <div className="sidebar-bottom"><div className="help-link"><CircleHelp size={17} /><span>Help center</span></div><div className="user-chip"><span className="avatar">JD</span><span><strong>Jordan Davis</strong><small>Energy manager</small></span><button className="sign-out" onClick={() => setSignedIn(false)} aria-label="Sign out" title="Sign out"><LogOut size={15} /></button></div></div>
    </aside>
    <section className="content-area">
      <header className="topbar"><button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open navigation"><Menu size={20} /></button><div><p className="eyebrow">Friday, October 18, 2024</p><h1>{activePage === 'Overview' ? 'Good morning, Jordan' : activePage}</h1></div><div className="top-actions"><button className="icon-button" aria-label="Notifications"><Bell size={19} /><i /></button><div className="top-avatar">JD</div></div></header>
      {activePage !== 'Overview' ? <PlaceholderPage page={activePage} onBack={() => selectPage('Overview')} /> : <><div className="status-strip"><span className="status-dot" /><strong>All systems operational</strong><span className="status-separator" /><span>Last synced 4 min ago</span><button>View system health <ArrowUpRight size={14} /></button></div><div className="content-grid">
        <section className="hero-panel"><div className="hero-copy"><span className="section-kicker">ENERGY SNAPSHOT <Activity size={14} /></span><h2>Campus energy is<br /><em>trending efficiently.</em></h2><p>Consumption is down 12.4% compared to this time last week.</p><div className="hero-metric"><strong>847</strong><span>kWh<br /><small>used today</small></span></div></div><div className="hero-chart"><div className="chart-topline"><span>Today's load profile</span><span className="chart-legend"><i /> Actual <i className="forecast-dot" /> Forecast</span></div><div className="bar-chart">{bars.map((height, index) => <div className={`bar ${index > 15 ? 'forecast' : ''}`} key={index} style={{ '--bar-height': `${height}%` }} />)}</div><div className="chart-axis"><span>12 AM</span><span>6 AM</span><span>12 PM</span><span>6 PM</span><span>Now</span></div></div></section>
        <div className="kpi-grid"><KpiCard label="Energy cost" value="$124.80" change="8.2%" detail="vs last week" positive icon={<Activity size={18} />} /><KpiCard label="Carbon avoided" value="426 kg" change="14.6%" detail="vs last week" positive icon={<Leaf size={18} />} /><KpiCard label="Peak demand" value="186 kW" change="5.1%" detail="vs last week" icon={<ThermometerSun size={18} />} /></div>
        <section className="panel buildings-panel"><PanelHeading title="Building performance" action="View all buildings" /><div className="building-list"><BuildingRow name="Innovation Hall" type="Academic · 42,000 sq ft" value="218 kWh" percent="82%" color="lime" /><BuildingRow name="Student Commons" type="Dining & social · 28,500 sq ft" value="164 kWh" percent="64%" color="mint" /><BuildingRow name="Research Center" type="Labs · 61,200 sq ft" value="149 kWh" percent="58%" color="amber" /></div></section>
        <section className="panel insight-panel"><div className="insight-heading"><span className="spark-icon"><Sparkles size={17} /></span><div><span className="section-kicker">AI RECOMMENDATION</span><h3>One action can save $38 today</h3></div></div><p>Pre-cool Innovation Hall by 2°C before 4 PM peak demand. Occupancy patterns suggest the building will be 22% empty.</p><div className="insight-footer"><span><CloudSun size={16} /> Confidence: 94%</span><button onClick={() => setShowApproval(true)} className={approved ? 'approved' : ''}>{approved ? <><Check size={15} /> Approved</> : <><Play size={14} /> Review action</>}</button></div></section>
        <section className="panel alerts-panel"><PanelHeading title="Recent alerts" action="See all alerts" /><div className="alert-row"><span className="alert-icon amber"><ThermometerSun size={16} /></span><span><strong>Unusual HVAC load detected</strong><small>Innovation Hall · 12 minutes ago</small></span><span className="severity">Review</span></div><div className="alert-row"><span className="alert-icon green"><TrendingDown size={16} /></span><span><strong>Demand response target met</strong><small>Campus-wide · 1 hour ago</small></span><span className="severity resolved">Resolved</span></div></section>
      </div></>}
    </section>
    {showApproval && <div className="modal-backdrop" onClick={() => setShowApproval(false)}><div className="approval-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setShowApproval(false)} aria-label="Close"><X size={18} /></button><span className="modal-icon"><Sparkles size={20} /></span><span className="section-kicker">AI RECOMMENDATION</span><h2>Approve pre-cooling action?</h2><p>EcoMind will adjust Innovation Hall's HVAC setpoint to 20°C from 3:30 PM to 4:30 PM.</p><div className="modal-impact"><span>Estimated savings</span><strong>$38.00</strong></div><div className="modal-actions"><button className="button-secondary" onClick={() => setShowApproval(false)}>Not now</button><button className="button-primary" onClick={() => { setApproved(true); setShowApproval(false) }}><Check size={16} /> Approve action</button></div></div></div>}
  </main>
}

function KpiCard({ label, value, change, detail, positive, icon }) { return <article className="kpi-card"><div className="kpi-head"><span>{label}</span><span className="kpi-icon">{icon}</span></div><strong className="kpi-value">{value}</strong><div className="kpi-change"><span className={positive ? 'positive' : 'negative'}>{positive ? '↓' : '↑'} {change}</span><span>{detail}</span></div></article> }
function BuildingRow({ name, type, value, percent, color }) { return <div className="building-row"><span className={`building-avatar ${color}`}><Building2 size={18} /></span><span className="building-name"><strong>{name}</strong><small>{type}</small></span><span className="load-track"><i style={{ width: percent }} /></span><span className="building-value"><strong>{value}</strong><small>{percent} load</small></span></div> }
function PanelHeading({ title, action }) { return <div className="panel-heading"><h3>{title}</h3><button>{action} <ArrowUpRight size={14} /></button></div> }
function PlaceholderPage({ page, onBack }) { return <div className="placeholder"><div className="placeholder-icon"><Settings size={22} /></div><span className="section-kicker">ECOMIND WORKSPACE</span><h2>{page} is ready for your campus data.</h2><p>This view is wired into the navigation and ready for the next operational workflow.</p><button className="button-primary" onClick={onBack}>Back to overview <ArrowUpRight size={15} /></button></div> }
function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const handleSubmit = (event) => {
    event.preventDefault()
    if (!email || !password) { setError('Enter your email and password to continue.'); return }
    setError('')
    onLogin()
  }
  return <main className="login-shell"><div className="login-visual"><div className="login-brand"><span className="brand-mark"><Leaf size={17} /></span><span>ecomind<span className="brand-dot">.</span></span></div><div className="visual-copy"><span className="section-kicker">CAMPUS ENERGY INTELLIGENCE</span><h1>Make every<br /><em>watt matter.</em></h1><p>See the whole picture. Act on what matters. Build a more efficient campus with intelligence on your side.</p></div><div className="visual-foot"><span><Activity size={15} /> Live energy operations</span><span>North Campus · 2024</span></div></div><section className="login-form-wrap"><div className="login-form-card"><div className="mobile-login-brand"><span className="brand-mark"><Leaf size={17} /></span><span>ecomind<span className="brand-dot">.</span></span></div><span className="section-kicker">WELCOME BACK</span><h2>Sign in to your workspace</h2><p className="login-subtitle">Your campus is waiting.</p><form onSubmit={handleSubmit}><label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@university.edu" autoComplete="email" /></label><label>Password<span className="password-input"><input type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" autoComplete="current-password" /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></span></label><div className="login-options"><label className="remember"><input type="checkbox" /> <span>Remember me</span></label><button type="button" className="forgot">Forgot password?</button></div>{error && <p className="login-error" role="alert">{error}</p>}<button className="login-submit" type="submit"><LockKeyhole size={16} /> Sign in</button></form><p className="login-help">Need access? <button type="button">Contact your campus admin</button></p></div></section></main>
}

export default App
