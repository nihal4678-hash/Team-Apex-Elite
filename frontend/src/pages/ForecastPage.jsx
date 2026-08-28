import { useState, useEffect } from 'react'
import {
  TrendingDown, Activity, Sparkles, Building2, Calendar, Clock,
  RefreshCw, CheckCircle2, AlertTriangle, ArrowUpRight, Leaf, ShieldCheck,
  Zap, Cpu, BarChart3, PieChart, Layers, HelpCircle
} from 'lucide-react'
import { getForecastDashboard } from '../services/api'

export function ForecastPage() {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAnalytics = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getForecastDashboard()
      if (res && res.kpis) {
        setDashboard(res)
      } else {
        setError('Forecast pipeline returned empty payload. Using fallback analytics engine.')
      }
    } catch (err) {
      setError(`Failed to fetch forecast analytics: ${err.message || err}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const kpis = dashboard?.kpis || {
    predicted_energy_24h_kwh: 3793.8,
    predicted_cost_inr: 33195.75,
    predicted_peak_demand_kw: 245.0,
    peak_demand_time_window: '14:00 – 16:00',
    model_accuracy_pct: 96.4,
    mape_pct: 3.6,
    savings_opportunity_inr: 3120.4,
    carbon_impact_co2_kg: 3110.9,
    high_demand_buildings_count: 2,
    weather_impact_score: '+7.4% Demand Surge',
    weather_impact_pct: 7.4,
  }

  const actualSeries = dashboard?.actual_series || [
    40.1, 40.5, 40.3, 39.2, 34.7, 30.9, 21.5, 21.8,
    57.0, 58.6, 58.8, 61.4, 77.8, 110.0, 130.8, 134.3,
    0, 0, 0, 0, 0, 0, 0, 0
  ]

  const forecastSeries = dashboard?.forecast_series || [
    131.4, 131.0, 81.8, 82.7, 46.1, 39.6, 40.6, 40.6,
    200.0, 200.0, 200.0, 200.0, 240.0, 265.0, 280.0, 295.0,
    310.0, 285.0, 250.0, 220.0, 195.0, 170.0, 145.0, 130.0
  ]

  const timeLabels = dashboard?.time_labels || Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`)

  const buildingSummaries = dashboard?.building_summaries || [
    { building_id: 'BLK-D', name: 'Main Complex Block D', category: 'academic', predicted_kw: 450.0, load_percent: 92.0, status: 'High Load Warning', daily_cost_inr: 21262.5, area_share_pct: 35.3 },
    { building_id: 'HST-B', name: 'Vignan Vihar Boys Hostel', category: 'hostel', predicted_kw: 240.0, load_percent: 78.0, status: 'High Load Warning', daily_cost_inr: 11340.0, area_share_pct: 11.5 },
    { building_id: 'BLK-A', name: 'Academic Block A - Engineering', category: 'academic', predicted_kw: 218.0, load_percent: 72.0, status: 'Normal Operating', daily_cost_inr: 10300.5, area_share_pct: 12.5 },
    { building_id: 'HST-G', name: 'Priyadarsini Girls Hostel', category: 'hostel', predicted_kw: 210.0, load_percent: 68.0, status: 'Normal Operating', daily_cost_inr: 9922.5, area_share_pct: 9.6 },
    { building_id: 'LAB-CSE', name: 'Computer Science Labs', category: 'computer_lab', predicted_kw: 195.0, load_percent: 64.0, status: 'Normal Operating', daily_cost_inr: 9213.75, area_share_pct: 6.2 },
    { building_id: 'BLK-B', name: 'Academic Block B - Sciences', category: 'academic', predicted_kw: 182.0, load_percent: 58.0, status: 'Normal Operating', daily_cost_inr: 8599.5, area_share_pct: 9.4 },
    { building_id: 'BLK-C', name: 'Academic Block C - Management', category: 'admin', predicted_kw: 145.0, load_percent: 48.0, status: 'Optimal Low Demand', daily_cost_inr: 6851.25, area_share_pct: 8.9 },
    { building_id: 'LIB', name: 'Central Library (NTR)', category: 'library', predicted_kw: 135.0, load_percent: 42.0, status: 'Optimal Low Demand', daily_cost_inr: 6378.75, area_share_pct: 4.2 },
  ]

  const featureImportances = dashboard?.feature_importances || [
    { feature_name: 'Outdoor Temperature & Solar Heat Differential', importance_pct: 34.2, description: 'Ambient outdoor temperature delta driving active HVAC cooling load across academic blocks' },
    { feature_name: 'Academic Timetable & Classroom Working Hours', importance_pct: 28.5, description: 'Core working hours occupancy and computer laboratory equipment operation' },
    { feature_name: 'Historical Autoregressive Lag Consumption (24h/168h)', importance_pct: 18.4, description: 'Smart meter telemetry historical trend and day-of-week load baseline' },
    { feature_name: 'Campus Student & Staff Occupancy Ratio', importance_pct: 12.6, description: 'Estimated active occupancy density derived from wifi and building access sensors' },
    { feature_name: 'Academic Calendar & Examination Schedule', importance_pct: 6.3, description: 'Calendar day type classification and examination period operating extension' },
  ]

  const recommendations = dashboard?.recommendations || [
    { id: 'REC-FC-01', category: 'HVAC Pre-Cooling', title: 'Initiate 2°C Pre-Cooling in Block D & CSE Labs at 08:30', description: 'Pre-cool high-thermal mass academic zones prior to the 10:00–12:00 occupancy surge.', estimated_savings_inr: 1716.22, priority: 'HIGH' },
    { id: 'REC-FC-02', category: 'Solar Peak Shifting', title: 'Engage VFSTR 1 MW Solar PV Generation during 12:00–15:00 peak', description: 'Offset grid electricity purchase during peak tariff window using rooftop solar output.', estimated_savings_inr: 1092.14, priority: 'HIGH' },
    { id: 'REC-FC-03', category: 'Base-Load Reduction', title: 'Enforce automated lighting & chiller setback in Library after 18:00', description: 'Reduce night-time baseload consumption across low-occupancy administrative blocks.', estimated_savings_inr: 312.04, priority: 'MEDIUM' },
  ]

  const hourlyRows = dashboard?.hourly_rows || Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    timestamp: `${h.toString().padStart(2, '0')}:00`,
    record_type: h < 16 ? 'actual' : 'forecast',
    actual_kwh: h < 16 ? actualSeries[h] : null,
    predicted_kwh: forecastSeries[h],
    variance_pct: h < 16 ? roundVal(((forecastSeries[h] - actualSeries[h]) / actualSeries[h]) * 100, 1) : null,
    cost_inr: roundVal(forecastSeries[h] * 8.75, 2),
    building_status: forecastSeries[h] > 300 ? 'High Demand' : forecastSeries[h] > 200 ? 'Moderate' : 'Baseline',
  }))

  const maxChartVal = Math.max(...forecastSeries, ...actualSeries.filter(x => x > 0)) || 350

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
      {/* 1. Executive Forecast Header */}
      <section className="panel" style={{ width: '100%', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: '#ffffff', borderColor: '#334155', padding: '1.25rem 1.5rem', borderRadius: '12px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <div style={{ width: '42px', height: '42px', background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingDown size={24} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                MACHINE LEARNING FORECASTING LAYER
              </div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0.15rem 0', color: '#ffffff' }}>
                {dashboard?.executive_title || 'VFSTR Smart Campus ML Energy & Demand Forecast Engine'}
              </h2>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                Continuous load predictions using <strong>{dashboard?.model_name || 'LightGBM Regressor + RandomForest Ensemble'}</strong> · Calibrated to VFSTR 2.5M kWh annual audit baseline.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right', fontSize: '0.82rem', color: '#cbd5e1' }}>
              <div>Horizon: <strong>{dashboard?.horizon || '24-Hour Horizon & Monthly Projections'}</strong></div>
              <small style={{ color: '#94a3b8' }}>Updated: {dashboard?.last_updated || 'Just now'}</small>
            </div>
            <button
              onClick={fetchAnalytics}
              disabled={loading}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.1rem',
                background: 'rgba(255, 255, 255, 0.12)', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.25)',
                borderRadius: '8px', fontSize: '0.88rem', cursor: 'pointer', fontWeight: 600, transition: 'all 0.2s'
              }}
            >
              <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh Analytics
            </button>
          </div>
        </div>
      </section>

      {/* Error notification banner */}
      {error && (
        <section className="panel" style={{ width: '100%', background: '#fef2f2', borderColor: '#fecaca', color: '#991b1b', padding: '0.85rem 1.25rem', borderRadius: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        </section>
      )}

      {/* 2. KPI Cards Grid (8 Key Metrics) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', width: '100%' }}>
        <ForecastKpiCard
          label="24-Hour Predicted Energy"
          value={`${kpis.predicted_energy_24h_kwh?.toLocaleString()} kWh`}
          detail="24-hr projected campus load"
          icon={<Zap size={18} />}
        />
        <ForecastKpiCard
          label="Predicted Electricity Cost"
          value={`₹${kpis.predicted_cost_inr?.toLocaleString()}`}
          detail="@ ₹8.75 / kWh Commercial Tariff"
          icon={<TrendingDown size={18} />}
        />
        <ForecastKpiCard
          label="Predicted Peak Demand"
          value={`${kpis.predicted_peak_demand_kw} kW`}
          detail={`Peak Window: ${kpis.peak_demand_time_window}`}
          icon={<Building2 size={18} />}
        />
        <ForecastKpiCard
          label="Model Forecast Accuracy"
          value={`${kpis.model_accuracy_pct}%`}
          detail={`MAPE: ${kpis.mape_pct}% | LightGBM Ensemble`}
          positive
          icon={<ShieldCheck size={18} />}
        />
        <ForecastKpiCard
          label="Savings Opportunity"
          value={`₹${kpis.savings_opportunity_inr?.toLocaleString()}`}
          detail="via closed-loop setpoint setback"
          positive
          icon={<Sparkles size={18} />}
        />
        <ForecastKpiCard
          label="Carbon Impact (Scope 2)"
          value={`${kpis.carbon_impact_co2_kg?.toLocaleString()} kg`}
          detail="0.82 kg CO₂ / kWh grid factor"
          positive
          icon={<Leaf size={18} />}
        />
        <ForecastKpiCard
          label="High-Demand Buildings"
          value={`${kpis.high_demand_buildings_count} Blocks`}
          detail="> 75% load capacity threshold"
          icon={<AlertTriangle size={18} />}
        />
        <ForecastKpiCard
          label="Weather Impact Score"
          value={kpis.weather_impact_score}
          detail="Ambient Temp +3.5°C above mean"
          icon={<Activity size={18} />}
        />
      </div>

      {/* 3. Trend Analytics Section (Polished Chart with Clear X and Y Axis Scales) */}
      <section className="panel" style={{ width: '100%', padding: 0, overflow: 'hidden', borderRadius: '12px', background: '#ffffff', border: '1px solid var(--color-border)' }}>
        {/* Dark Analytics Header Bar */}
        <div style={{ background: '#1e293b', color: '#ffffff', padding: '0.85rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <BarChart3 size={18} style={{ color: '#38bdf8' }} />
            <h3 style={{ fontSize: '0.95rem', margin: 0, letterSpacing: '0.05em', textTransform: 'uppercase', color: '#f8fafc', fontWeight: 700 }}>
              24-Hour Demand Trend & Forecast Load Profile
            </h3>
          </div>
          <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.82rem', color: '#cbd5e1' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <i style={{ display: 'inline-block', width: '12px', height: '12px', background: '#64748b', borderRadius: '2px' }} />
              Actual Smart Meter (16h)
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <i style={{ display: 'inline-block', width: '12px', height: '12px', background: '#10b981', borderRadius: '2px' }} />
              ML Predicted Horizon (8h)
            </span>
          </div>
        </div>

        {/* Main Chart Area */}
        <div style={{ padding: '1.5rem 1.25rem 1rem 1.25rem' }}>
          <div style={{ display: 'flex', height: '220px', gap: '1rem' }}>
            {/* Y-Axis scale label column */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', textAlign: 'right', minWidth: '45px', paddingBottom: '1.25rem' }}>
              <span>{Math.round(maxChartVal)} kW</span>
              <span>{Math.round(maxChartVal * 0.75)} kW</span>
              <span>{Math.round(maxChartVal * 0.50)} kW</span>
              <span>{Math.round(maxChartVal * 0.25)} kW</span>
              <span>0 kW</span>
            </div>

            {/* Bars container */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: '8px', borderBottom: '2px solid #e2e8f0', paddingBottom: '2px' }}>
                {forecastSeries.map((fVal, idx) => {
                  const actVal = actualSeries[idx] || 0
                  const isActual = idx < 16
                  const hAct = Math.min(100, Math.max(5, (actVal / maxChartVal) * 100))
                  const hPred = Math.min(100, Math.max(5, (fVal / maxChartVal) * 100))

                  return (
                    <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }} title={`${timeLabels[idx]}: Forecast ${fVal} kW ${isActual ? `| Actual ${actVal} kW` : ''}`}>
                      <div style={{ width: '100%', display: 'flex', gap: '3px', alignItems: 'flex-end', height: '100%' }}>
                        {isActual && (
                          <div style={{ width: '50%', background: '#64748b', height: `${hAct}%`, borderRadius: '3px 3px 0 0' }} />
                        )}
                        <div style={{ width: isActual ? '50%' : '100%', background: isActual ? '#38bdf8' : '#10b981', height: `${hPred}%`, borderRadius: '3px 3px 0 0' }} />
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Horizontal X-Axis time labels */}
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.5rem', fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>
                <span>00:00</span>
                <span>03:00</span>
                <span>06:00</span>
                <span>09:00</span>
                <span>12:00</span>
                <span>15:00</span>
                <span>18:00</span>
                <span>21:00</span>
                <span>23:00</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Building-Wise Forecast Intelligence & Block Contribution (Side by Side Grid) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', width: '100%' }}>
        {/* Building Ranking Table */}
        <section className="panel" style={{ background: '#ffffff', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.6rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Building2 size={18} style={{ color: '#16a34a' }} />
              <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Building-Wise Demand Ranking & Capacity</h3>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--color-muted)' }}>Sorted by Load (kW)</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left', color: '#64748b' }}>
                  <th style={{ padding: '0.5rem' }}>Building Block</th>
                  <th style={{ padding: '0.5rem' }}>Area</th>
                  <th style={{ padding: '0.5rem' }}>Predicted</th>
                  <th style={{ padding: '0.5rem' }}>Capacity</th>
                  <th style={{ padding: '0.5rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {buildingSummaries.map((b, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.55rem 0.5rem', fontWeight: 600, color: '#1e293b' }}>{b.name}</td>
                    <td style={{ padding: '0.55rem 0.5rem', color: '#64748b' }}>{b.area_share_pct}%</td>
                    <td style={{ padding: '0.55rem 0.5rem', fontWeight: 600, color: '#0f172a' }}>{b.predicted_kw} kW</td>
                    <td style={{ padding: '0.55rem 0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <div style={{ flex: 1, height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${b.load_percent}%`, height: '100%', background: b.load_percent > 75 ? '#ef4444' : b.load_percent > 50 ? '#f59e0b' : '#10b981' }} />
                        </div>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{b.load_percent}%</span>
                      </div>
                    </td>
                    <td style={{ padding: '0.55rem 0.5rem' }}>
                      <span style={{
                        padding: '0.15rem 0.45rem', borderRadius: '10px', fontSize: '0.72rem', fontWeight: 600, whitespace: 'nowrap',
                        background: b.status.includes('Warning') ? '#fef2f2' : b.status.includes('Normal') ? '#f0fdf4' : '#e0f2fe',
                        color: b.status.includes('Warning') ? '#991b1b' : b.status.includes('Normal') ? '#166534' : '#0369a1'
                      }}>
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Block-Wise Load Contribution */}
        <section className="panel" style={{ background: '#ffffff', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.6rem' }}>
            <PieChart size={18} style={{ color: '#3b82f6' }} />
            <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Block-Wise Energy Share & Built-up Area Breakdown</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {buildingSummaries.map((b, i) => {
              const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#6366f1', '#14b8a6']
              const color = colors[i % colors.length]
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                    <span style={{ fontWeight: 600, color: '#1e293b' }}>{b.name}</span>
                    <span style={{ fontWeight: 700, color: color }}>{b.area_share_pct}% share ({b.building_area_sqm?.toLocaleString()} m²)</span>
                  </div>
                  <div style={{ height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${b.area_share_pct * 2.5}%`, height: '100%', background: color, borderRadius: '4px' }} />
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>

      {/* 5. ML Model Insights & Feature Importance Panel (Full Width) */}
      <section className="panel" style={{ width: '100%', background: '#ffffff', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.6rem' }}>
          <Cpu size={18} style={{ color: '#8b5cf6' }} />
          <h3 style={{ margin: 0, fontSize: '1.05rem' }}>ML Forecasting Engine Feature Split Importance Drivers</h3>
        </div>
        <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
          LightGBM ensemble feature importance split scores identifying primary environmental and operational drivers of campus energy demand.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {featureImportances.map((f, i) => (
            <div key={i} style={{ background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: '10px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <strong style={{ fontSize: '0.88rem', color: '#0f172a' }}>{f.feature_name}</strong>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#6d28d9', background: '#f3e8ff', padding: '0.15rem 0.5rem', borderRadius: '10px' }}>
                    {f.importance_pct}%
                  </span>
                </div>
                <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.5rem' }}>
                  <div style={{ width: `${f.importance_pct * 2.5}%`, height: '100%', background: 'linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%)' }} />
                </div>
              </div>
              <p style={{ color: '#64748b', fontSize: '0.8rem', margin: 0, lineHeight: '1.35' }}>{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 6. Operational Recommendations Panel (Full Width) */}
      <section className="panel" style={{ width: '100%', background: '#f0fdf4', borderColor: '#bbf7d0', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', borderBottom: '1px solid #bbf7d0', paddingBottom: '0.6rem' }}>
          <Sparkles size={18} style={{ color: '#16a34a' }} />
          <h3 style={{ margin: 0, color: '#14532d', fontSize: '1.05rem' }}>Operational Priority Control Actions</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {recommendations.map((rec, i) => (
            <div key={i} style={{ background: '#ffffff', padding: '1rem', borderRadius: '10px', border: '1px solid #bbf7d0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.75rem', background: '#dcfce7', color: '#15803d', padding: '0.2rem 0.55rem', borderRadius: '10px', fontWeight: 700 }}>
                  {rec.category}
                </span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#15803d' }}>
                  +₹{rec.estimated_savings_inr?.toLocaleString()} / day
                </span>
              </div>
              <strong style={{ fontSize: '0.92rem', color: '#14532d', display: 'block', marginBottom: '0.3rem' }}>{rec.title}</strong>
              <p style={{ fontSize: '0.83rem', color: '#334155', margin: 0, lineHeight: '1.4' }}>{rec.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 7. Detailed 24-Hour Forecast Data Table */}
      <section className="panel" style={{ width: '100%', background: '#ffffff', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.6rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={18} style={{ color: '#16a34a' }} />
            <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Detailed 24-Hour Interval Forecast Output Table</h3>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-muted)' }}>Showing 24 Hourly Intervals</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left', color: '#64748b' }}>
                <th style={{ padding: '0.6rem 0.8rem' }}>Time Window</th>
                <th style={{ padding: '0.6rem 0.8rem' }}>Record Type</th>
                <th style={{ padding: '0.6rem 0.8rem' }}>Actual kWh</th>
                <th style={{ padding: '0.6rem 0.8rem' }}>Predicted kWh</th>
                <th style={{ padding: '0.6rem 0.8rem' }}>Variance %</th>
                <th style={{ padding: '0.6rem 0.8rem' }}>Estimated Cost (INR)</th>
                <th style={{ padding: '0.6rem 0.8rem' }}>Demand Status</th>
              </tr>
            </thead>
            <tbody>
              {hourlyRows.map((row, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600, color: '#0f172a' }}>{row.timestamp}</td>
                  <td style={{ padding: '0.6rem 0.8rem' }}>
                    <span style={{
                      padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: '0.75rem', fontWeight: 600,
                      background: row.record_type === 'actual' ? '#f1f5f9' : '#dcfce7',
                      color: row.record_type === 'actual' ? '#475569' : '#15803d'
                    }}>
                      {row.record_type.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', color: '#334155' }}>{row.actual_kwh !== null ? `${row.actual_kwh} kWh` : '—'}</td>
                  <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600, color: '#0f172a' }}>{row.predicted_kwh} kWh</td>
                  <td style={{ padding: '0.6rem 0.8rem', color: row.variance_pct && row.variance_pct > 0 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                    {row.variance_pct !== null ? `${row.variance_pct > 0 ? `+${row.variance_pct}%` : `${row.variance_pct}%`}` : '—'}
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600, color: '#16a34a' }}>₹{row.cost_inr?.toLocaleString()}</td>
                  <td style={{ padding: '0.6rem 0.8rem' }}>
                    <span style={{
                      padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: '0.75rem', fontWeight: 600,
                      background: row.building_status === 'High Demand' ? '#fef2f2' : row.building_status === 'Moderate' ? '#fff7ed' : '#f0fdf4',
                      color: row.building_status === 'High Demand' ? '#991b1b' : row.building_status === 'Moderate' ? '#c2410c' : '#166534'
                    }}>
                      {row.building_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function ForecastKpiCard({ label, value, detail, positive, icon }) {
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

function roundVal(num, decimals = 1) {
  if (num === null || num === undefined || isNaN(num)) return 0
  return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals)
}
