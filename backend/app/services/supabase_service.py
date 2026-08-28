import json
import logging
import urllib.request
import urllib.error
from typing import Any

from app.core.config import settings

logger = logging.getLogger("ecomind.supabase")


class SupabaseService:
    """Additive Supabase client for storing simulation-generated data with fallback handling."""

    def __init__(self):
        self.url = settings.SUPABASE_URL.rstrip('/') if settings.SUPABASE_URL else ""
        self.key = settings.SUPABASE_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def _post(self, table: str, payload: list[dict] | dict) -> dict[str, Any]:
        """Post data to a Supabase REST endpoint via HTTP."""
        if not self.is_configured:
            return {
                "success": False,
                "status": "not_configured",
                "message": "Supabase URL and API key not configured. Using local DB persistence."
            }

        endpoint = f"{self.url}/rest/v1/{table}"
        data_bytes = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=data_bytes,
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 201, 204):
                    return {
                        "success": True,
                        "status": "stored_supabase",
                        "records_count": len(payload) if isinstance(payload, list) else 1,
                        "message": f"Successfully stored in Supabase table '{table}'."
                    }
                return {
                    "success": False,
                    "status": "http_error",
                    "code": response.status,
                    "message": f"Supabase responded with HTTP {response.status}"
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
            logger.warning("Supabase HTTP post error for table '%s' (%s): %s", table, e.code, err_body)
            return {
                "success": False,
                "status": "http_error",
                "code": e.code,
                "message": f"Supabase HTTP {e.code}: {err_body[:200]}"
            }
        except Exception as e:
            logger.warning("Supabase connection fallback for table '%s': %s", table, e)
            return {
                "success": False,
                "status": "connection_error",
                "message": f"Supabase connection warning: {e}"
            }

    def _delete(self, table: str, query_params: str) -> dict[str, Any]:
        """Delete matching records from Supabase REST endpoint via HTTP DELETE."""
        if not self.is_configured:
            return {"success": False, "status": "not_configured"}

        endpoint = f"{self.url}/rest/v1/{table}?{query_params}"
        req = urllib.request.Request(
            endpoint,
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
            },
            method="DELETE"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return {"success": response.status in (200, 204), "status": response.status}
        except Exception as e:
            logger.warning("Supabase DELETE error for '%s?%s': %s", table, query_params, e)
            return {"success": False, "error": str(e)}

    def store_simulated_readings(self, scenario_id: str, readings: list[dict]) -> dict[str, Any]:
        """Store simulation-generated preprocessed readings in Supabase."""
        if not readings:
            return {"success": True, "status": "empty", "stored_count": 0}

        # Tag explicitly with data_source="simulated"
        formatted = []
        for r in readings:
            item = dict(r)
            item["scenario_id"] = scenario_id
            item["data_source"] = "simulated"
            formatted.append(item)

        # Batch insert to Supabase
        batch_size = 100
        stored_total = 0
        last_result = None

        for i in range(0, len(formatted), batch_size):
            batch = formatted[i:i + batch_size]
            res = self._post("simulated_preprocessed_readings", batch)
            last_result = res
            if res.get("success"):
                stored_total += len(batch)

        if stored_total > 0:
            return {
                "success": True,
                "status": "stored_supabase",
                "stored_count": stored_total,
                "message": f"Stored {stored_total} simulation records in Supabase (data_source='simulated')."
            }

        return {
            "success": False,
            "status": last_result.get("status", "fallback_local") if last_result else "not_configured",
            "stored_count": 0,
            "message": last_result.get("message", "Supabase offline. Stored in local DB with data_source='simulated'.") if last_result else "Supabase not configured."
        }

    def store_simulation_run(self, metadata: dict) -> dict[str, Any]:
        """Store simulation run metadata in Supabase."""
        payload = dict(metadata)
        payload["data_source"] = "simulated_vignan_loop"
        return self._post("simulation_scenario_runs", payload)

    def delete_simulated_records(self, scenario_id: str = None) -> dict[str, Any]:
        """Safely delete simulation records from Supabase where data_source='simulated'."""
        if not self.is_configured:
            return {"success": False, "status": "not_configured"}

        if scenario_id:
            res1 = self._delete("simulated_preprocessed_readings", f"scenario_id=eq.{scenario_id}")
            res2 = self._delete("simulation_scenario_runs", f"scenario_id=eq.{scenario_id}")
        else:
            res1 = self._delete("simulated_preprocessed_readings", "data_source=eq.simulated")
            res2 = self._delete("simulation_scenario_runs", "data_source=eq.simulated_vignan_loop")

        return {"success": res1.get("success") or res2.get("success")}


supabase_service = SupabaseService()
