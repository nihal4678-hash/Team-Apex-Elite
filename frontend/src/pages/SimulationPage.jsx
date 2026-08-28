import { useState, useEffect, useRef } from 'react'
import {
  SlidersHorizontal, Play, Square, RotateCcw, Calendar, Clock, Building2, Sparkles,
  AlertTriangle, CheckCircle2, TrendingDown, Leaf, Activity, ArrowUpRight, Database,
  RefreshCw, Layers, Trash2, ShieldAlert
} from 'lucide-react'
import {
  startControlledSimulation, stopControlledSimulation, getSimulationProgress,
  getSimulationScenarios, cleanupSimulationRecords, getLoopScenarioDetail
} from '../services/api'

export function SimulationPage({ buildings = [], onNavigateToAlerts }) {
  // Input State
  const [fromDate, setFromDate] = useState('2025-07-01')
  const [fromTime, setFromTime] = useState('08:00')
  const [toDate, setToDate] = useState('2025-07-31')
  const [toTime, setToTime] = useState('18:00')
  const [selectedBuilding, setSelectedBuilding] = useState('ALL')
  const [tempDelta, setTempDelta] = useState(-2.0)
  const [occupancyScale, setOccupancyScale] = useState(1.0)
  const [includeSolar, setIncludeSolar] = useState(true)
  const [afterHoursMonitoring, setAfterHoursMonitoring] = useState(true)
  const [cleanPrevious, setCleanPrevious] = useState(false)

  // Live Control & Progress State
  const [runStatus, setRunStatus] = useState('Ready')  // Ready, Validating, Running, Stopping, Stopped, Completed, Failed
  const [activeScenarioId, setActiveScenarioId] = useState(null)
  const [progressData, setProgressData] = useState(null)
  const [simData, setSimData] = useState(null)
  const [scenarioHistory, setScenarioHistory] = useState([])

  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const pollIntervalRef = useRef(null)

  const buildingOptions = [
    { id: 'ALL', name: 'All Vignan Campus Blocks (111,916 m²)' },
    { id: 'academic', name: 'Academic Blocks (Blocks A, B, D)' },
    { id: 'LAB-CSE', name: 'CSE / Laboratory Block (6,943 m²)' },
    { id: 'BLK-C', name: 'Administrative Block C (9,936 m²)' },
    { id: 'LIB', name: 'Central Library NTR (4,722 m²)' },
    { id: 'hostel', name: 'Hostel Complexes (Girls & Boys)' },
  ]

  const loadScenarios = async () => {
    const history = await getSimulationScenarios()
    if (history) setScenarioHistory(history)
  }

  useEffect(() => {
    loadScenarios()
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [])

  // Poll real-time progress while simulation status is running or stopping
  useEffect(() => {
    if (activeScenarioId && (runStatus === 'Running' || runStatus === 'Stopping')) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const prog = await getSimulationProgress(activeScenarioId)
          if (prog) {
            setProgressData(prog)
            if (prog.status === 'completed') {
              setRunStatus('Completed')
              clearInterval(pollIntervalRef.current)
              setNotice(`Simulation scenario '${activeScenarioId}' completed successfully!`)
              await loadCompletedResults(activeScenarioId)
              await loadScenarios()
            } else if (prog.status === 'stopped') {
              setRunStatus('Stopped')
              clearInterval(pollIntervalRef.current)
              setNotice(`Simulation stopped safely. Completed ${prog.completed_hourly_records} / ${prog.total_hourly_records} hourly records preserved.`)
              await loadCompletedResults(activeScenarioId)
              await loadScenarios()
            } else if (prog.status === 'failed') {
              setRunStatus('Failed')
              clearInterval(pollIntervalRef.current)
              setError(prog.failure_message || 'Simulation execution failed.')
            } else if (prog.status === 'stopping') {
              setRunStatus('Stopping')
            }
          }
        } catch (err) {
          console.warn('Progress poll warning:', err)
        }
      }, 1000)
    } else {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [activeScenarioId, runStatus])

  const loadCompletedResults = async (scenarioId) => {
    try {
      const detail = await getLoopScenarioDetail(scenarioId)
      if (detail) {
        setSimData({
          run_id: detail.scenario_id,
          scenario_id: detail.scenario_id,
          building_name: selectedBuilding === 'ALL' ? 'All Vignan Campus Blocks' : selectedBuilding,
          from_date: fromDate,
          to_date: toDate,
          total_records: detail.preprocessed_records_stored,
          predicted_energy_kwh: detail.total_predicted_kwh,
          predicted_cost_inr: detail.total_predicted_kwh * 8.75,
          estimated_saved_kwh: detail.total_saved_kwh,
          estimated_saved_inr: detail.total_saved_inr,
          carbon_avoided_kg: detail.total_co2_reduced_kg,
          peak_demand_kw: 215.0,
          persistence_status: `Stored ${detail.preprocessed_records_stored} hourly records in database.`,
        })
      }
    } catch (e) {
      console.warn('Load results detail fallback:', e)
    }
  }

  const handleStartSimulation = async (e) => {
    e.preventDefault()
    setError(null)
    setNotice(null)
    setSimData(null)

    if (!fromDate || !toDate) {
      setError('Please select valid From Date and To Date.')
      return
    }

    setRunStatus('Validating')

    try {
      const res = await startControlledSimulation({
        from_date: fromDate,
        from_time: fromTime,
        to_date: toDate,
        to_time: toTime,
        building_id: selectedBuilding,
        temperature_delta: parseFloat(tempDelta),
        occupancy_scale: parseFloat(occupancyScale),
        include_solar: includeSolar,
        after_hours_monitoring: afterHoursMonitoring,
        clean_previous: cleanPrevious,
      })

      if (res && res.scenario_id) {
        setActiveScenarioId(res.scenario_id)
        setRunStatus('Running')
        setNotice(`Controlled simulation launched (Scenario ID: ${res.scenario_id}). Processing live hourly records...`)
      } else {
        setRunStatus('Failed')
        setError('Failed to initiate controlled simulation job.')
      }
    } catch (err) {
      setRunStatus('Failed')
      setError(`Simulation start failed: ${err.message || err}`)
    }
  }

  const handleStopSimulation = async () => {
    if (!activeScenarioId) return
    setRunStatus('Stopping')
    try {
      const res = await stopControlledSimulation(activeScenarioId)
      if (res && res.success) {
        setNotice(`Stop signal sent for ${activeScenarioId}. Finishing current hourly record safely...`)
      }
    } catch (err) {
      setError(`Failed to send stop signal: ${err.message || err}`)
    }
  }

  const handleResetForm = () => {
    setFromDate('2025-07-01')
    setFromTime('08:00')
    setToDate('2025-07-31')
    setToTime('18:00')
    setSelectedBuilding('ALL')
    setTempDelta(-2.0)
    setOccupancyScale(1.0)
    setIncludeSolar(true)
    setAfterHoursMonitoring(true)
    setCleanPrevious(false)
    setRunStatus('Ready')
    setActiveScenarioId(null)
    setProgressData(null)
    setSimData(null)
    setError(null)
    setNotice(null)
  }

  const handleClearHistory = async () => {
    if (!window.confirm('Clear all previous simulation records from Supabase and database?')) return
    try {
      const res = await cleanupSimulationRecords()
      if (res && res.success) {
        setSimData(null)
        setProgressData(null)
        await loadScenarios()
        setNotice('Successfully cleared simulation history.')
      }
    } catch (err) {
      setError(`Failed to clear history: ${err.message || err}`)
    }
  }

  const isRunning = runStatus === 'Running' || runStatus === 'Stopping'

  return (
    <div className="content-grid" style={{ gap: '1.5rem' }}>
      {/* 1. Simulation Control Panel */}
      <section className="panel" style={{ gridColumn: 'span 12', background: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ padding: '0.4rem', background: '#f0fdf4', color: '#16a34a', borderRadius: '8px', display: 'inline-flex' }}>
              <SlidersHorizontal size={20} />
            </span>
            <div>
              <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Controlled Live Hourly Simulation & Anomaly Processing Engine</h2>
              <small style={{ color: 'var(--color-muted)' }}>Calibrated to VFSTR 2.5M kWh Audit Baseline · Live Progress & Real-Time Alert Stream</small>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{
              fontSize: '0.8rem', padding: '0.3rem 0.75rem', borderRadius: '12px', fontWeight: 700, textTransform: 'uppercase',
              background: isRunning ? '#fef3c7' : runStatus === 'Completed' ? '#dcfce7' : runStatus === 'Stopped' ? '#fee2e2' : '#f1f5f9',
              color: isRunning ? '#b45309' : runStatus === 'Completed' ? '#15803d' : runStatus === 'Stopped' ? '#b91c1c' : '#475569'
            }}>
              Status: {runStatus}
            </span>
          </div>
        </div>

        <form onSubmit={handleStartSimulation}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            {/* From Date & Time */}
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                <Calendar size={14} style={{ display: 'inline', marginRight: '0.3rem', color: '#16a34a' }} /> From Date & Time
              </label>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <input
                  type="date"
                  value={fromDate}
                  disabled={isRunning}
                  onChange={(e) => setFromDate(e.target.value)}
                  style={{ flex: 2, padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.88rem' }}
                  required
                />
                <input
                  type="time"
                  value={fromTime}
                  disabled={isRunning}
                  onChange={(e) => setFromTime(e.target.value)}
                  style={{ flex: 1, padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.88rem' }}
                  required
                />
              </div>
            </div>

            {/* To Date & Time */}
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                <Calendar size={14} style={{ display: 'inline', marginRight: '0.3rem', color: '#16a34a' }} /> To Date & Time
              </label>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <input
                  type="date"
                  value={toDate}
                  disabled={isRunning}
                  onChange={(e) => setToDate(e.target.value)}
                  style={{ flex: 2, padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.88rem' }}
                  required
                />
                <input
                  type="time"
                  value={toTime}
                  disabled={isRunning}
                  onChange={(e) => setToTime(e.target.value)}
                  style={{ flex: 1, padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.88rem' }}
                  required
                />
              </div>
            </div>

            {/* Select Block / Scope */}
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                <Building2 size={14} style={{ display: 'inline', marginRight: '0.3rem', color: '#16a34a' }} /> Select Block / Scope
              </label>
              <select
                value={selectedBuilding}
                disabled={isRunning}
                onChange={(e) => setSelectedBuilding(e.target.value)}
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid var(--color-border)', fontSize: '0.88rem', background: '#fff' }}
              >
                {buildingOptions.map((opt) => (
                  <option key={opt.id} value={opt.id}>{opt.name}</option>
                ))}
              </select>
            </div>

            {/* HVAC Setpoint Adjustment */}
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                HVAC Setpoint: <strong>{tempDelta}°C</strong>
              </label>
              <input
                type="range"
                min="-4.0"
                max="2.0"
                step="0.5"
                disabled={isRunning}
                value={tempDelta}
                onChange={(e) => setTempDelta(e.target.value)}
                style={{ width: '100%', marginTop: '0.4rem' }}
              />
            </div>

            {/* Toggles */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', paddingTop: '0.2rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 600, color: '#334155' }}>
                <input
                  type="checkbox"
                  checked={includeSolar}
                  disabled={isRunning}
                  onChange={(e) => setIncludeSolar(e.target.checked)}
                  style={{ accentColor: '#16a34a' }}
                />
                Include VFSTR 1 MW Solar PV Offset
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 600, color: '#334155' }}>
                <input
                  type="checkbox"
                  checked={afterHoursMonitoring}
                  disabled={isRunning}
                  onChange={(e) => setAfterHoursMonitoring(e.target.checked)}
                  style={{ accentColor: '#16a34a' }}
                />
                Include After-Hours Night Leak Monitoring
              </label>
            </div>
          </div>

          {/* Action Buttons Toolbar (Start, Stop right beside Start, Reset) */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.75rem', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
            <button
              type="button"
              onClick={handleResetForm}
              disabled={isRunning}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.65rem 1.1rem', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', cursor: 'pointer', fontWeight: 600 }}
            >
              <RotateCcw size={16} /> Reset Form
            </button>

            <button
              type="button"
              onClick={handleStopSimulation}
              disabled={!isRunning}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.65rem 1.3rem',
                background: isRunning ? '#ef4444' : '#f8fafc', color: isRunning ? '#ffffff' : '#94a3b8',
                border: '1px solid #dc2626', borderRadius: '8px', fontSize: '0.9rem', cursor: isRunning ? 'pointer' : 'not-allowed', fontWeight: 600
              }}
            >
              <Square size={16} /> Stop Simulation
            </button>

            <button
              type="submit"
              className="button-primary"
              disabled={isRunning}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 1.5rem', fontSize: '0.95rem' }}
            >
              {isRunning ? (
                <>
                  <RefreshCw size={17} className="spin-icon" /> Running Simulation Loop...
                </>
              ) : (
                <>
                  <Play size={17} /> Start Simulation
                </>
              )}
            </button>
          </div>
        </form>

        {notice && (
          <div style={{ marginTop: '1rem', padding: '0.85rem 1rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#15803d', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={18} />
            <span>{notice}</span>
          </div>
        )}

        {error && (
          <div style={{ marginTop: '1rem', padding: '0.85rem 1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}
      </section>

      {/* 2. Prominent Live Progress Box */}
      {(progressData || isRunning) && (
        <section className="panel" style={{ gridColumn: 'span 12', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#ffffff', borderColor: '#334155', borderRadius: '12px', padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <span className="section-kicker" style={{ color: '#38bdf8' }}>LIVE SIMULATION PROGRESS MONITOR</span>
              <h3 style={{ margin: '0.2rem 0', color: '#ffffff' }}>Scenario ID: {progressData?.scenario_id || activeScenarioId}</h3>
              <small style={{ color: '#94a3b8' }}>Scope: {selectedBuilding} · {fromDate} {fromTime} to {toDate} {toTime}</small>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8' }}>
                {progressData?.completion_percentage || 0}%
              </span>
              <small style={{ display: 'block', color: '#94a3b8' }}>Completion Percentage</small>
            </div>
          </div>

          {/* Progress Bar */}
          <div style={{ width: '100%', height: '10px', background: '#334155', borderRadius: '5px', overflow: 'hidden', marginBottom: '1.25rem' }}>
            <div style={{ width: `${progressData?.completion_percentage || 0}%`, height: '100%', background: 'linear-gradient(90deg, #38bdf8 0%, #22c55e 100%)', transition: 'width 0.4s ease-in-out' }} />
          </div>

          {/* Live Counter Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <small style={{ color: '#94a3b8', display: 'block' }}>Hours Completed</small>
              <strong style={{ fontSize: '1.1rem', color: '#f8fafc' }}>{progressData?.completed_hourly_records || 0} / {progressData?.total_hourly_records || 1}</strong>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <small style={{ color: '#94a3b8', display: 'block' }}>Current Processing</small>
              <strong style={{ fontSize: '0.9rem', color: '#38bdf8' }}>{progressData?.current_timestamp || 'Initializing...'}</strong>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <small style={{ color: '#94a3b8', display: 'block' }}>Rows Stored</small>
              <strong style={{ fontSize: '1.1rem', color: '#4ade80' }}>{progressData?.generated_records_count || 0}</strong>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <small style={{ color: '#94a3b8', display: 'block' }}>Alerts Detected</small>
              <strong style={{ fontSize: '1.1rem', color: '#f87171' }}>{progressData?.alerts_detected_count || 0}</strong>
            </div>
          </div>
        </section>
      )}

      {/* 3. Output Dashboard Cards (Completed or Stopped Simulation Results) */}
      {simData && (
        <div className="kpi-grid" style={{ gridColumn: 'span 12' }}>
          <SimKpiCard label="Predicted Energy" value={`${(simData.predicted_energy_kwh || 0).toLocaleString()} kWh`} detail="VFSTR Audit Anchored" icon={<Activity size={18} />} />
          <SimKpiCard label="Predicted Electricity Cost" value={`₹${(simData.predicted_cost_inr || 0).toLocaleString()}`} detail="@ ₹8.75 / kWh Tariff" icon={<TrendingDown size={18} />} />
          <SimKpiCard label="Estimated Energy Savings" value={`${(simData.estimated_saved_kwh || 0).toLocaleString()} kWh`} detail="via setpoint setback" positive icon={<Sparkles size={18} />} />
          <SimKpiCard label="Estimated Cost Savings" value={`₹${(simData.estimated_saved_inr || 0).toLocaleString()}`} detail="monetary reduction" positive icon={<ArrowUpRight size={18} />} />
          <SimKpiCard label="Carbon Avoided" value={`${(simData.carbon_avoided_kg || 0).toLocaleString()} kg`} detail="CO₂ reduction" positive icon={<Leaf size={18} />} />
          <SimKpiCard label="Peak Demand" value={`${simData.peak_demand_kw || 186} kW`} detail="maximum hourly kW" icon={<Building2 size={18} />} />
        </div>
      )}

      {/* 4. Saved Scenarios & Alert Navigation */}
      <section className="panel" style={{ gridColumn: 'span 12' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={18} style={{ color: '#16a34a' }} />
            <h3>Saved Simulation Scenarios & Live Alert Links</h3>
          </div>

          <button onClick={handleClearHistory} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.4rem 0.8rem', background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca', borderRadius: '6px', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 600 }}>
            <Trash2 size={15} /> Clear Simulation History
          </button>
        </div>

        {scenarioHistory.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left', color: 'var(--color-muted)' }}>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Scenario ID</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Run Status</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Saved Energy (kWh)</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Saved Cost (INR)</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>CO₂ Avoided (kg)</th>
                  <th style={{ padding: '0.6rem 0.8rem' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {scenarioHistory.map((sc, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600 }}>{sc.scenario_id}</td>
                    <td style={{ padding: '0.6rem 0.8rem' }}>
                      <span style={{
                        padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase',
                        background: sc.status === 'completed' ? '#f0fdf4' : sc.status === 'stopped' ? '#fef2f2' : '#fefce8',
                        color: sc.status === 'completed' ? '#16a34a' : sc.status === 'stopped' ? '#991b1b' : '#854d0e'
                      }}>
                        {sc.status || 'completed'}
                      </span>
                    </td>
                    <td style={{ padding: '0.6rem 0.8rem' }}>{(sc.total_saved_kwh || 0).toLocaleString()} kWh</td>
                    <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600, color: '#16a34a' }}>₹{(sc.total_saved_inr || 0).toLocaleString()}</td>
                    <td style={{ padding: '0.6rem 0.8rem' }}>{(sc.total_co2_reduced_kg || 0).toLocaleString()} kg</td>
                    <td style={{ padding: '0.6rem 0.8rem' }}>
                      {onNavigateToAlerts && (
                        <button
                          onClick={() => onNavigateToAlerts(sc.scenario_id)}
                          style={{ padding: '0.25rem 0.6rem', background: '#e0f2fe', color: '#0369a1', border: 'none', borderRadius: '4px', fontSize: '0.78rem', cursor: 'pointer', fontWeight: 600 }}
                        >
                          View Alerts
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--color-muted)', fontSize: '0.9rem', margin: 0 }}>No saved simulation runs in database.</p>
        )}
      </section>
    </div>
  )
}

function SimKpiCard({ label, value, detail, positive, icon }) {
  return (
    <article className="kpi-card" style={{ background: '#ffffff', borderRadius: '10px', padding: '1rem', border: '1px solid var(--color-border)' }}>
      <div className="kpi-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>{label}</span>
        <span className="kpi-icon" style={{ color: '#16a34a' }}>{icon}</span>
      </div>
      <strong className="kpi-value" style={{ fontSize: '1.35rem', fontWeight: 700, color: '#0f172a', display: 'block' }}>{value}</strong>
      <div className="kpi-change" style={{ marginTop: '0.3rem', fontSize: '0.78rem' }}>
        <span className={positive ? 'positive' : 'negative'} style={{ color: positive ? '#16a34a' : '#64748b' }}>
          {positive ? '↓' : '•'} {detail}
        </span>
      </div>
    </article>
  )
}
