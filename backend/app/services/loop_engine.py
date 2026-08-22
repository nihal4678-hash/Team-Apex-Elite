from datetime import datetime, timezone
from app.services import ml_bridge


class ClosedLoopEngine:
    def __init__(self):
        self.applied_actions: dict[str, dict] = {}
        self.resolved_alerts: set[str] = set()
        self.custom_building_loads: dict[str, float] = {}
        self.extra_saved_kwh: float = 0.0
        self.extra_saved_money_inr: float = 0.0
        self.extra_saved_co2_kg: float = 0.0

    def get_building_list(self) -> list[dict]:
        df = ml_bridge.load_buildings_df()
        if df.empty:
            return [
                {"id": "BLK-A", "name": "Academic Block A", "category": "academic", "kw": 218, "load": 82, "status": "normal"},
                {"id": "LAB-CSE", "name": "Computer Science Lab", "category": "computer_lab", "kw": 164, "load": 64, "status": "normal"},
                {"id": "LIB", "name": "Central Library", "category": "library", "kw": 149, "load": 58, "status": "normal"},
            ]

        results = []
        for idx, row in df.iterrows():
            b_id = str(row.get("building_id", f"b-{idx}"))
            b_name = str(row.get("building_name", b_id))
            b_cat = str(row.get("category", "academic"))
            area = float(row.get("area_sqm", 5000))
            
            # Base load calculation
            base_kw = round(area * 0.015, 1)
            # Apply loop modification if an action affected this building
            if b_id in self.custom_building_loads:
                base_kw = self.custom_building_loads[b_id]
            
            # Calculate load percentage relative to baseline capacity
            max_cap = area * 0.025 if area > 0 else 100
            load_pct = min(99, max(15, int((base_kw / max_cap) * 100)))
            status = "high" if load_pct > 80 else ("warning" if load_pct > 70 else "normal")

            results.append({
                "id": b_id,
                "name": b_name,
                "category": b_cat,
                "area_sqm": area,
                "kw": base_kw,
                "load": load_pct,
                "status": status,
            })
        return results

    def get_campus_snapshot(self) -> dict:
        weekly = ml_bridge.load_weekly_report_json()
        monthly = weekly.get("monthly_savings", {})
        
        base_kwh = monthly.get("energy_kwh", 6347.03) + self.extra_saved_kwh
        base_inr = monthly.get("money_inr", 55536.51) + self.extra_saved_money_inr
        base_co2 = monthly.get("co2_kg", 5204.56) + self.extra_saved_co2_kg

        return {
            "energy_used_today_kwh": 847.0,
            "energy_saved_month_kwh": round(base_kwh, 2),
            "energy_cost_today_inr": 124.80,
            "money_saved_month_inr": round(base_inr, 2),
            "carbon_avoided_kg": round(base_co2, 2),
            "peak_demand_kw": 186.0,
            "weekly_change_percent": -12.4,
            "active_actions_count": len(self.applied_actions),
            "resolved_alerts_count": len(self.resolved_alerts),
        }

    def get_load_forecast(self) -> dict:
        df = ml_bridge.load_forecast_df()
        if not df.empty and "predicted_energy_kwh" in df.columns:
            # Group hourly average forecast
            df_hourly = df.groupby("hour")["predicted_energy_kwh"].mean().reset_index()
            df_hourly["actual"] = df.groupby("hour")["energy_kwh"].mean().values
            actuals = [round(v, 1) for v in df_hourly["actual"].head(16).tolist()]
            forecasts = [round(v, 1) for v in df_hourly["predicted_energy_kwh"].tail(8).tolist()]
            return {"actual": actuals, "forecast": forecasts}
        
        return {
            "actual": [52, 61, 57, 66, 72, 69, 78, 74, 83, 79, 88, 84, 91, 86, 94, 90],
            "forecast": [82, 76, 69, 62, 56, 49, 45, 42]
        }

    def get_alerts(self) -> list[dict]:
        df = ml_bridge.load_alerts_df()
        alerts_list = []
        
        if not df.empty:
            # Filter distinct interesting alerts
            sample_df = df.head(15)
            for idx, row in sample_df.iterrows():
                alert_id = f"ALT-{idx+100}"
                status = "resolved" if alert_id in self.resolved_alerts else "pending"
                alerts_list.append({
                    "id": alert_id,
                    "building_id": str(row.get("building_id", "BLK-A")),
                    "building": str(row.get("building_name", "Academic Block A")),
                    "type": str(row.get("injected_fault", "Spike")).replace("_", " ").title(),
                    "severity": str(row.get("severity", "medium")).lower(),
                    "message": str(row.get("reason", "Load baseline variance")),
                    "recommended_action": str(row.get("recommended_action", "Verify controls")),
                    "estimated_waste_kwh": round(float(row.get("estimated_waste_kwh", 2.5)), 2),
                    "estimated_cost_inr": round(float(row.get("estimated_cost_inr", 21.8)), 2),
                    "status": status,
                })
        else:
            alerts_list = [
                {
                    "id": "ALT-101",
                    "building_id": "LAB-CSE",
                    "building": "Computer Science Laboratories",
                    "type": "Unusual HVAC Load",
                    "severity": "critical",
                    "message": "HVAC running after hours with low occupancy",
                    "recommended_action": "Raise setpoint by 2°C",
                    "estimated_waste_kwh": 4.5,
                    "estimated_cost_inr": 39.38,
                    "status": "pending" if "ALT-101" not in self.resolved_alerts else "resolved",
                }
            ]
        return alerts_list

    def get_recommendations(self) -> list[dict]:
        recs = ml_bridge.load_recommendations_json()
        for item in recs:
            rec_id = item.get("recommendation_id")
            item["applied"] = rec_id in self.applied_actions
            if item["applied"]:
                item["applied_at"] = self.applied_actions[rec_id].get("applied_at")
        return recs

    def apply_action(self, action_id: str, params: dict = None) -> dict:
        """Closed-Loop Feedback: Applies an action, adjusts load state, & updates metrics."""
        now_str = datetime.now(timezone.utc).isoformat()
        recs = ml_bridge.load_recommendations_json()
        target_rec = next((r for r in recs if r.get("recommendation_id") == action_id), None)
        
        saved_kwh = target_rec.get("energy_saved_kwh", 150.0) if target_rec else 150.0
        saved_inr = target_rec.get("money_saved_inr", 1312.5) if target_rec else 1312.5
        saved_co2 = target_rec.get("co2_reduced_kg", 123.0) if target_rec else 123.0

        # Update feedback loop state
        self.applied_actions[action_id] = {
            "applied_at": now_str,
            "saved_kwh": saved_kwh,
            "saved_inr": saved_inr,
            "saved_co2": saved_co2,
            "params": params or {}
        }
        
        self.extra_saved_kwh += saved_kwh
        self.extra_saved_money_inr += saved_inr
        self.extra_saved_co2_kg += saved_co2

        # Dynamically reduce load for affected buildings in closed loop
        if target_rec:
            for b in target_rec.get("buildings", []):
                self.custom_building_loads[b] = max(50.0, self.custom_building_loads.get(b, 150.0) * 0.88)

        return {
            "success": True,
            "action_id": action_id,
            "status": "applied",
            "saved_kwh": saved_kwh,
            "saved_inr": saved_inr,
            "saved_co2_kg": saved_co2,
            "applied_at": now_str,
        }

    def resolve_alert(self, alert_id: str) -> dict:
        self.resolved_alerts.add(alert_id)
        return {"success": True, "alert_id": alert_id, "status": "resolved"}

    def run_simulation(self, building_id: str, temp_delta: float, duration_minutes: int) -> dict:
        """Simulates closed-loop environmental control & energy reduction."""
        base_kw = self.custom_building_loads.get(building_id, 200.0)
        # Rule: Every 1 deg C temperature raise reduces HVAC load by ~6%
        saving_pct = abs(temp_delta) * 0.06
        saved_kw = base_kw * saving_pct
        saved_kwh = saved_kw * (duration_minutes / 60.0)
        saved_inr = saved_kwh * 8.75
        saved_co2 = saved_kwh * 0.82

        return {
            "building_id": building_id,
            "temp_delta": temp_delta,
            "duration_minutes": duration_minutes,
            "saved_kwh": round(saved_kwh, 2),
            "estimated_savings_inr": round(saved_inr, 2),
            "co2_reduced_kg": round(saved_co2, 2),
            "status": "simulation_complete",
        }


# Global closed-loop engine instance
loop_engine_instance = ClosedLoopEngine()
