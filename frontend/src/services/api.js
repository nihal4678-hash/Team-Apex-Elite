const API_BASE_URL = 'http://localhost:8000/api';

async function fetchJson(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API call failed: ${res.status} ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`[EcoMind API Bridge] Fallback mode for ${endpoint}:`, err.message);
    return null;
  }
}

export async function getCampusSnapshot() {
  const data = await fetchJson('/snapshot');
  if (data) return data;
  return {
    energy_used_today_kwh: 847,
    energy_saved_month_kwh: 6347.03,
    energy_cost_today_inr: 124.80,
    money_saved_month_inr: 55536.51,
    carbon_avoided_kg: 426,
    peak_demand_kw: 186,
    weekly_change_percent: -12.4,
  };
}

export async function getBuildings() {
  const data = await fetchJson('/buildings');
  if (data) return data;
  return [
    { id: 'BLK-A', name: 'Academic Block A — Engineering', load: 82, kw: 218, status: 'high' },
    { id: 'LAB-CSE', name: 'Computer Science Laboratories', load: 64, kw: 164, status: 'normal' },
    { id: 'LIB', name: 'Central Library', load: 58, kw: 149, status: 'normal' },
  ];
}

export async function getForecast() {
  const data = await fetchJson('/forecast');
  if (data) return data;
  return {
    actual: [52, 61, 57, 66, 72, 69, 78, 74, 83, 79, 88, 84, 91, 86, 94, 90],
    forecast: [82, 76, 69, 62, 56, 49, 45, 42],
  };
}

export async function getForecastDashboard() {
  const data = await fetchJson('/forecast/dashboard');
  return data || null;
}

export async function getAlerts() {
  const data = await fetchJson('/alerts');
  if (data) return data;
  return [
    {
      id: 'ALT-101',
      building: 'Computer Science Laboratories',
      type: 'Unusual HVAC load detected',
      severity: 'critical',
      message: 'HVAC running after hours with low occupancy',
      status: 'pending',
    },
  ];
}

export async function getAlertsDashboard() {
  const data = await fetchJson('/alerts/dashboard');
  return data || null;
}

export async function sendAlertFeedback(alertId, feedback, notes = '') {
  const data = await fetchJson(`/alerts/${alertId}/feedback`, {
    method: 'POST',
    body: JSON.stringify({ user_feedback: feedback, notes }),
  });
  return data || { success: true };
}

export async function getRecommendations() {
  const data = await fetchJson('/recommendations');
  if (data) return data;
  return [
    {
      recommendation_id: 'REC-HVAC-001',
      title: 'After-hours HVAC setback',
      description: 'Lock AC except hostels and exam-critical labs after 18:00; raise setpoint to 28°C.',
      money_saved_inr: 4805.61,
      co2_reduced_kg: 450.35,
      priority_score: 98,
    },
  ];
}

export async function applyRecommendation(actionId, params = {}) {
  const data = await fetchJson('/recommendations/apply', {
    method: 'POST',
    body: JSON.stringify({ action_id: actionId, params }),
  });
  return data || { success: true, action_id: actionId, status: 'applied' };
}

export async function resolveAlert(alertId) {
  const data = await fetchJson(`/alerts/${alertId}/resolve`, {
    method: 'POST',
  });
  return data || { success: true, alert_id: alertId, status: 'resolved' };
}

export async function runSimulation(buildingId, tempDelta = -2, durationMinutes = 60) {
  const data = await fetchJson('/simulation', {
    method: 'POST',
    body: JSON.stringify({
      building_id: buildingId,
      temperature_delta: tempDelta,
      duration_minutes: durationMinutes,
    }),
  });
  return data || { building_id: buildingId, estimated_savings: 38, status: 'ready_for_approval' };
}

export async function runDateRangeSimulation(params = {}) {
  const payload = {
    from_date: params.from_date || '2025-07-01',
    from_time: params.from_time || '08:00',
    to_date: params.to_date || '2025-07-31',
    to_time: params.to_time || '18:00',
    building_id: params.building_id || 'ALL',
    temperature_delta: params.temperature_delta ?? -2.0,
    occupancy_scale: params.occupancy_scale ?? 1.0,
    include_solar: params.include_solar ?? true,
    after_hours_monitoring: params.after_hours_monitoring ?? true,
    clean_previous: params.clean_previous ?? false,
  };

  const data = await fetchJson('/simulation/loop/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  return data;
}

export async function startControlledSimulation(params = {}) {
  const payload = {
    from_date: params.from_date || '2025-07-01',
    from_time: params.from_time || '08:00',
    to_date: params.to_date || '2025-07-31',
    to_time: params.to_time || '18:00',
    building_id: params.building_id || 'ALL',
    temperature_delta: params.temperature_delta ?? -2.0,
    occupancy_scale: params.occupancy_scale ?? 1.0,
    include_solar: params.include_solar ?? true,
    after_hours_monitoring: params.after_hours_monitoring ?? true,
    clean_previous: params.clean_previous ?? false,
  };

  const data = await fetchJson('/simulation/loop/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data;
}

export async function stopControlledSimulation(scenarioId) {
  const data = await fetchJson(`/simulation/loop/stop?scenario_id=${scenarioId}`, {
    method: 'POST',
  });
  return data;
}

export async function getSimulationProgress(scenarioId) {
  const data = await fetchJson(`/simulation/loop/progress/${scenarioId}`);
  return data;
}

export async function getSimulationScenarios() {
  const data = await fetchJson('/simulation/loop/scenarios');
  return data || [];
}

export async function getLoopScenarioDetail(scenarioId) {
  const data = await fetchJson(`/simulation/loop/scenario/${scenarioId}`);
  return data || null;
}

export async function cleanupSimulationRecords(scenarioId = null) {
  const url = scenarioId ? `/simulation/loop/cleanup?scenario_id=${scenarioId}` : '/simulation/loop/cleanup';
  const data = await fetchJson(url, { method: 'DELETE' });
  return data || { success: true };
}

export async function getSustainability() {
  const data = await fetchJson('/sustainability');
  if (data) return data;
  return {
    carbon_avoided_kg: 426,
    energy_intensity: '12.4% below baseline',
  };
}

export async function getAnalyticsSummary() {
  return await fetchJson('/analytics/summary');
}

export async function getAgentRuns() {
  return await fetchJson('/agent/runs');
}

export async function triggerAgentRun(stage = null) {
  return await fetchJson('/agent/run', {
    method: 'POST',
    body: JSON.stringify({ stage }),
  });
}

// --- GEMINI INTELLIGENCE API CALLS ---
export async function getGeminiCostExplanation() {
  return await fetchJson('/ai/cost-explanation');
}

export async function getGeminiAnomalySummary() {
  return await fetchJson('/ai/anomaly-summary');
}

export async function getGeminiApprovalSupport(recommendationId) {
  return await fetchJson('/ai/approval-support', {
    method: 'POST',
    body: JSON.stringify({ recommendation_id: recommendationId }),
  });
}

export async function getGeminiScenarioAnalysis() {
  return await fetchJson('/ai/scenario');
}

export async function getGeminiExecutiveReport() {
  return await fetchJson('/ai/report');
}

export async function askGeminiQuestion(question) {
  return await fetchJson('/ai/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}
