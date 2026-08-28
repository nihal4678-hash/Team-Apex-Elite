import { useState, useEffect } from 'react'
import {
  Bell, AlertTriangle, ShieldCheck, ThermometerSun, RefreshCw, Filter,
  Building2, Calendar, Clock, ArrowUpRight, Zap, Info, CheckCircle2,
  X, Layers, Activity, Eye, FileText, Check, ThumbsUp, ThumbsDown
} from 'lucide-react'
import { getAlertsDashboard, sendAlertFeedback, resolveAlert } from '../services/api'

export function AlertsPage({ onResolveAlert, initialScenarioId = null }) {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filter States
  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [sourceFilter, setSourceFilter] = useState('ALL')
  const [scenarioFilter, setScenarioFilter] = useState(initialScenarioId || 'ALL')

  // Selected Alert Modal / Drawer State
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [feedbackSuccess, setFeedbackSuccess] = useState(null)
  const [processingId, setProcessingId] = useState(null)

  const fetchDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getAlertsDashboard()
      if (res && res.kpis) {
        setDashboard(res)
      } else {
        setError('Alerts engine returned empty response. Using fallback data.')
      }
    } catch (err) {
      setError(`Failed to load context-aware alerts: ${err.message || err}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  const handleFeedback = async (alertId, feedbackType) => {
    setProcessingId(alertId)
    setFeedbackSuccess(null)
    try {
      const res = await sendAlertFeedback(alertId, feedbackType)
      if (res && res.success) {
        setFeedbackSuccess(`Recorded feedback '${feedbackType}'. Model baseline updated.`)
        await fetchDashboard()
      }
    } catch (err) {
      alert(`Feedback submission error: ${err.message || err}`)
    } finally {
      setProcessingId(null)
    }
  }

  const kpis = dashboard?.kpis || {
    critical_alerts_count: 2,
    active_anomalies_count: 5,
    estimated_wasted_kwh: 485.4,
    estimated_avoidable_cost_inr: 4247.25,
    high_risk_buildings_count: 3
  }

  const rawAlerts = dashboard?.alerts || [
    {
      alert_id: 'ALT-201',
      building_id: 'BLK-D',
      building_name: 'Main Complex Block D',
      building_category: 'academic',
      timestamp: '2026-08-28 20:00:00',
      day_type: 'working_day',
      time_window: 'academic_after_hours',
      observed_kwh: 310.0,
      expected_kwh: 122.5,
      allowed_essential_kwh: 10.0,
      deviation_kwh: 187.5,
      deviation_ratio: 1.53,
      severity: 'critical',
      anomaly_type: 'After-Hours Academic Energy Leak',
      probable_cause: 'Possible lights, HVAC, lab equipment, or projectors left running after campus hours.',
      recommended_action: 'Inspect classroom and laboratory switches after 18:00.',
      status: 'new',
      user_feedback: null,
      confidence_score: 96.5,
      data_source: 'actual',
      created_at: '2026-08-28T20:00:00Z'
    },
    {
      alert_id: 'ALT-202',
      building_id: 'LAB-CSE',
      building_name: 'Computer Science Laboratories',
      building_category: 'computer_lab',
      timestamp: '2026-08-28 23:00:00',
      day_type: 'working_day',
      time_window: 'academic_night',
      observed_kwh: 145.0,
      expected_kwh: 45.0,
      allowed_essential_kwh: 14.0,
      deviation_kwh: 100.0,
      deviation_ratio: 2.22,
      severity: 'critical',
      anomaly_type: 'Continuous Overnight Load',
      probable_cause: 'Usage remains high for 3 or more consecutive night hours. Possible unmonitored equipment or chiller setback issue.',
      recommended_action: 'Verify night chiller setpoint and automated lighting shutdown.',
      status: 'new',
      user_feedback: null,
      confidence_score: 95.0,
      data_source: 'actual',
      created_at: '2026-08-28T23:00:00Z'
    },
    {
      alert_id: 'ALT-204',
      building_id: 'HST-G',
      building_name: 'Priyadarsini Girls Hostel Complex',
      building_category: 'hostel',
      timestamp: '2026-08-28 11:00:00',
      day_type: 'working_day',
      time_window: 'hostel_daytime',
      observed_kwh: 195.0,
      expected_kwh: 87.5,
      allowed_essential_kwh: 25.0,
      deviation_kwh: 107.5,
      deviation_ratio: 1.23,
      severity: 'anomaly',
      anomaly_type: 'Hostel Daytime Abnormality',
      probable_cause: 'Possible high occupancy, water pumping, common-area load, or appliance/HVAC overuse during class hours.',
      recommended_action: 'Inspect hostel common area pumps and AC units during class hours.',
      status: 'new',
      user_feedback: null,
      confidence_score: 92.0,
      data_source: 'actual',
      created_at: '2026-08-28T11:00:00Z'
    },
    {
      alert_id: 'ALT-205',
      building_id: 'HST-B',
      building_name: 'Vignan Vihar Boys Hostel Complex',
      building_category: 'hostel',
      timestamp: '2026-08-28 02:00:00',
      day_type: 'working_day',
      time_window: 'hostel_night',
      observed_kwh: 210.0,
      expected_kwh: 109.0,
      allowed_essential_kwh: 25.0,
      deviation_kwh: 101.0,
      deviation_ratio: 0.93,
      severity: 'warning',
      anomaly_type: 'Hostel Midnight Abnormality',
      probable_cause: 'Possible prolonged HVAC, common-area appliances, or abnormal floor-level consumption after midnight.',
      recommended_action: 'Check hostel common-area appliance schedules and floor meters.',
      status: 'investigating',
      user_feedback: null,
      confidence_score: 91.5,
      data_source: 'simulated',
      created_at: '2026-08-28T02:00:00Z'
    }
  ]

  // Filter Logic
  const filteredAlerts = rawAlerts.filter(a => {
    const matchesSearch = !searchQuery || a.building_name.toLowerCase().includes(searchQuery.toLowerCase()) || a.anomaly_type.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSev = severityFilter === 'ALL' || a.severity.toUpperCase() === severityFilter.toUpperCase()
    const matchesCat = categoryFilter === 'ALL' || a.building_category.toUpperCase() === categoryFilter.toUpperCase()
    const matchesSrc = sourceFilter === 'ALL' || a.data_source.toUpperCase() === sourceFilter.toUpperCase()
    const matchesScen = scenarioFilter === 'ALL' || !a.scenario_id || a.scenario_id.toUpperCase() === scenarioFilter.toUpperCase()
    return matchesSearch && matchesSev && matchesCat && matchesSrc && matchesScen
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
      {/* 1. Executive Alert Header */}
      <section className="panel" style={{ width: '100%', background: 'linear-gradient(135deg, #1e1b4b 0%, #311b92 100%)', color: '#ffffff', borderColor: '#4338ca', padding: '1.25rem 1.5rem', borderRadius: '12px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <div style={{ width: '42px', height: '42px', background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bell size={24} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#a5b4fc', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                CONTEXT-AWARE ANOMALY & LEAK DETECTION ENGINE
              </div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0.15rem 0', color: '#ffffff' }}>
                {dashboard?.executive_title || 'VFSTR Smart Campus Context-Aware Anomaly & Energy Leak Engine'}
              </h2>
              <div style={{ fontSize: '0.85rem', color: '#c7d2fe' }}>
                Evaluated against building type profiles, essential night-load allowances, and academic/hostel schedules.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right', fontSize: '0.82rem', color: '#e0e7ff' }}>
              <div>Evaluated: <strong>{dashboard?.last_evaluated || 'Just now'}</strong></div>
              <small style={{ color: '#a5b4fc' }}>Active Holidays Configured: {dashboard?.configurable_holidays?.length || 8}</small>
            </div>
            <button
              onClick={fetchDashboard}
              disabled={loading}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.1rem',
                background: 'rgba(255, 255, 255, 0.15)', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '8px', fontSize: '0.88rem', cursor: 'pointer', fontWeight: 600
              }}
            >
              <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              Re-scan Telemetry
            </button>
          </div>
        </div>
      </section>

      {/* Error notification banner if any */}
      {error && (
        <section className="panel" style={{ width: '100%', background: '#fef2f2', borderColor: '#fecaca', color: '#991b1b', padding: '0.85rem 1.25rem', borderRadius: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        </section>
      )}

      {/* 2. KPI Cards Grid (5 Summary Metrics) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', width: '100%' }}>
        <AlertKpiCard
          label="Critical Alerts"
          value={`${kpis.critical_alerts_count}`}
          detail="3+ hrs or > 2.0x threshold"
          urgent={kpis.critical_alerts_count > 0}
          icon={<AlertTriangle size={20} />}
        />
        <AlertKpiCard
          label="Active Anomalies"
          value={`${kpis.active_anomalies_count}`}
          detail="Exceeding context baseline"
          icon={<Activity size={20} />}
        />
        <AlertKpiCard
          label="Estimated Wasted Energy"
          value={`${kpis.estimated_wasted_kwh?.toLocaleString()} kWh`}
          detail="Cumulative excess over baseline"
          icon={<Zap size={20} />}
        />
        <AlertKpiCard
          label="Avoidable Cost Impact"
          value={`₹${kpis.estimated_avoidable_cost_inr?.toLocaleString()}`}
          detail="@ ₹8.75 / kWh AP Commercial"
          urgent={kpis.estimated_avoidable_cost_inr > 2000}
          icon={<ArrowUpRight size={20} />}
        />
        <AlertKpiCard
          label="High-Risk Buildings"
          value={`${kpis.high_risk_buildings_count} Blocks`}
          detail="Requiring facility inspection"
          icon={<Building2 size={20} />}
        />
      </div>

      {/* 3. Interactive Filter Toolbar */}
      <section className="panel" style={{ width: '100%', background: '#ffffff', padding: '1rem 1.25rem', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '240px', flex: 1 }}>
            <Filter size={18} style={{ color: '#64748b' }} />
            <input
              type="text"
              placeholder="Filter by building name or anomaly type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.88rem' }}
            />
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{ padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.85rem', background: '#fff' }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical Severity</option>
              <option value="ANOMALY">Anomaly Severity</option>
              <option value="WARNING">Warning Severity</option>
            </select>

            {/* Building Category Filter */}
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              style={{ padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.85rem', background: '#fff' }}
            >
              <option value="ALL">All Building Types</option>
              <option value="ACADEMIC">Academic Blocks</option>
              <option value="HOSTEL">Hostel Complexes</option>
              <option value="COMPUTER_LAB">Computer Science Labs</option>
              <option value="LIBRARY">Central Library</option>
              <option value="ADMIN">Admin Blocks</option>
            </select>

            {/* Data Source Toggle */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              style={{ padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.85rem', background: '#fff' }}
            >
              <option value="ALL">All Data Sources</option>
              <option value="ACTUAL">Actual Smart Meter</option>
              <option value="SIMULATED">Simulated Stream</option>
            </select>
          </div>
        </div>
      </section>

      {/* 4. Main Alert Log Table */}
      <section className="panel" style={{ width: '100%', background: '#ffffff', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.6rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={18} style={{ color: '#16a34a' }} />
            <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Context-Aware Telemetry Anomaly & Leak Log</h3>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-muted)' }}>Showing {filteredAlerts.length} of {rawAlerts.length} Anomaly Events</span>
        </div>

        {filteredAlerts.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left', color: '#64748b' }}>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Time & Building</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Type & Window</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Observed vs Expected</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Allowed Essential</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Deviation %</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Severity</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((al, idx) => {
                  const isCrit = al.severity === 'critical'
                  const isAnom = al.severity === 'anomaly'
                  const isWarn = al.severity === 'warning'
                  const sevColor = isCrit ? '#991b1b' : isAnom ? '#c2410c' : isWarn ? '#854d0e' : '#166534'
                  const sevBg = isCrit ? '#fef2f2' : isAnom ? '#fff7ed' : isWarn ? '#fefce8' : '#f0fdf4'

                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <strong style={{ display: 'block', color: '#0f172a' }}>{al.building_name}</strong>
                        <small style={{ color: '#64748b' }}>{al.timestamp} · Source: {al.data_source}</small>
                      </td>

                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <span style={{ fontWeight: 600, color: '#334155', display: 'block' }}>{al.anomaly_type}</span>
                        <small style={{ color: '#64748b', textTransform: 'capitalize' }}>{al.day_type.replace('_', ' ')} ({al.time_window.replace('_', ' ')})</small>
                      </td>

                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <strong style={{ color: '#0f172a' }}>{al.observed_kwh} kWh</strong>
                        <small style={{ display: 'block', color: '#64748b' }}>Exp: {al.expected_kwh} kWh</small>
                      </td>

                      <td style={{ padding: '0.65rem 0.8rem', color: '#16a34a', fontWeight: 600 }}>
                        {al.allowed_essential_kwh} kWh/hr
                      </td>

                      <td style={{ padding: '0.65rem 0.8rem', fontWeight: 700, color: sevColor }}>
                        +{Math.round(al.deviation_ratio * 100)}% (+{al.deviation_kwh} kWh)
                      </td>

                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <span style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', background: sevBg, color: sevColor }}>
                          {al.severity}
                        </span>
                      </td>

                      <td style={{ padding: '0.65rem 0.8rem' }}>
                        <button
                          onClick={() => setSelectedAlert(al)}
                          style={{
                            padding: '0.35rem 0.75rem', background: '#f1f5f9', color: '#1e293b',
                            border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600,
                            display: 'inline-flex', alignItems: 'center', gap: '0.3rem'
                          }}
                        >
                          <Eye size={14} /> Inspect & Feedback
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
            No anomaly events found matching current filter criteria.
          </div>
        )}
      </section>

      {/* 5. Alert Detail Modal / Drawer with Learning Loop Controls */}
      {selectedAlert && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.65)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem' }}>
          <div style={{ background: '#ffffff', borderRadius: '14px', width: '100%', maxWidth: '680px', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
            {/* Modal Header */}
            <div style={{ padding: '1.25rem 1.5rem', background: '#0f172a', color: '#ffffff', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTopLeftRadius: '14px', borderTopRightRadius: '14px' }}>
              <div>
                <span className="section-kicker" style={{ color: '#818cf8' }}>ALERT INSPECTOR & LEARNING LOOP</span>
                <h3 style={{ margin: '0.2rem 0', color: '#ffffff', fontSize: '1.15rem' }}>{selectedAlert.building_name} ({selectedAlert.alert_id})</h3>
              </div>
              <button onClick={() => { setSelectedAlert(null); setFeedbackSuccess(null); }} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0.2rem' }}>
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Alert Metrics Banner */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div>
                  <small style={{ color: '#64748b', display: 'block' }}>Observed Energy</small>
                  <strong style={{ fontSize: '1.2rem', color: '#0f172a' }}>{selectedAlert.observed_kwh} kWh</strong>
                </div>
                <div>
                  <small style={{ color: '#64748b', display: 'block' }}>Expected Baseline</small>
                  <strong style={{ fontSize: '1.2rem', color: '#16a34a' }}>{selectedAlert.expected_kwh} kWh</strong>
                </div>
                <div>
                  <small style={{ color: '#64748b', display: 'block' }}>Allowed Night Load</small>
                  <strong style={{ fontSize: '1.2rem', color: '#0284c7' }}>{selectedAlert.allowed_essential_kwh} kWh/hr</strong>
                </div>
              </div>

              {/* Context & Anomaly Explanation */}
              <div>
                <h4 style={{ fontSize: '0.92rem', color: '#1e293b', marginBottom: '0.3rem' }}>Context-Aware Baseline Evaluation:</h4>
                <p style={{ fontSize: '0.88rem', color: '#334155', background: '#f0fdf4', padding: '0.75rem 0.9rem', borderRadius: '8px', border: '1px solid #bbf7d0', margin: 0, lineHeight: '1.4' }}>
                  Evaluated as <strong>{selectedAlert.day_type.replace('_', ' ')}</strong> during <strong>{selectedAlert.time_window.replace('_', ' ')}</strong>. Expected baseline includes <strong>{selectedAlert.allowed_essential_kwh} kWh/hr permitted allowance</strong> for CCTV, security lighting, Wi-Fi routers, and emergency systems.
                </p>
              </div>

              {/* Probable Cause & Recommended Action */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ background: '#fff7ed', padding: '0.85rem', borderRadius: '8px', border: '1px solid #ffedd5' }}>
                  <h5 style={{ color: '#c2410c', margin: '0 0 0.3rem 0', fontSize: '0.85rem' }}>PROBABLE CAUSE IDENTIFIED</h5>
                  <p style={{ fontSize: '0.82rem', color: '#7c2d12', margin: 0, lineHeight: '1.35' }}>{selectedAlert.probable_cause}</p>
                </div>
                <div style={{ background: '#f0fdf4', padding: '0.85rem', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                  <h5 style={{ color: '#15803d', margin: '0 0 0.3rem 0', fontSize: '0.85rem' }}>RECOMMENDED ACTION</h5>
                  <p style={{ fontSize: '0.82rem', color: '#166534', margin: 0, lineHeight: '1.35' }}>{selectedAlert.recommended_action}</p>
                </div>
              </div>

              {/* Learning Loop / User Feedback Controls */}
              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '10px', border: '1px solid #cbd5e1' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#0f172a', margin: '0 0 0.4rem 0' }}>Learning Loop & Feedback Audit Decision:</h4>
                <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 0.85rem 0' }}>
                  Record facility administrator feedback to update building baseline configuration and prevent repeated false alerts.
                </p>

                {feedbackSuccess && (
                  <div style={{ marginBottom: '0.85rem', padding: '0.6rem 0.8rem', background: '#dcfce7', color: '#15803d', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <CheckCircle2 size={16} /> {feedbackSuccess}
                  </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem' }}>
                  <button
                    onClick={() => handleFeedback(selectedAlert.alert_id, 'genuine_anomaly')}
                    disabled={processingId === selectedAlert.alert_id}
                    style={{
                      padding: '0.55rem', background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca',
                      borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem'
                    }}
                  >
                    <AlertTriangle size={14} /> Genuine Anomaly
                  </button>

                  <button
                    onClick={() => handleFeedback(selectedAlert.alert_id, 'expected_usage')}
                    disabled={processingId === selectedAlert.alert_id}
                    style={{
                      padding: '0.55rem', background: '#f0fdf4', color: '#15803d', border: '1px solid #bbf7d0',
                      borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem'
                    }}
                  >
                    <CheckCircle2 size={14} /> Expected Event
                  </button>

                  <button
                    onClick={() => handleFeedback(selectedAlert.alert_id, 'false_positive')}
                    disabled={processingId === selectedAlert.alert_id}
                    style={{
                      padding: '0.55rem', background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd',
                      borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem'
                    }}
                  >
                    <ShieldCheck size={14} /> False Positive
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AlertKpiCard({ label, value, detail, urgent, icon }) {
  return (
    <article className="kpi-card" style={{ background: '#ffffff', borderRadius: '10px', padding: '1rem', border: urgent ? '1px solid #fecaca' : '1px solid var(--color-border)' }}>
      <div className="kpi-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>{label}</span>
        <span className="kpi-icon" style={{ color: urgent ? '#ef4444' : '#16a34a' }}>{icon}</span>
      </div>
      <strong className="kpi-value" style={{ fontSize: '1.35rem', fontWeight: 700, color: urgent ? '#991b1b' : '#0f172a', display: 'block' }}>{value}</strong>
      <div className="kpi-change" style={{ marginTop: '0.3rem', fontSize: '0.78rem' }}>
        <span className={urgent ? 'negative' : 'positive'} style={{ color: urgent ? '#ef4444' : '#16a34a' }}>
          • {detail}
        </span>
      </div>
    </article>
  )
}
