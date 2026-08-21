from app.models.building import Building


BUILDINGS = [
    Building(id="innovation-hall", name="Innovation Hall", building_type="Academic", area_sq_ft=42000, current_load_kw=218, load_percent=82),
    Building(id="student-commons", name="Student Commons", building_type="Dining & social", area_sq_ft=28500, current_load_kw=164, load_percent=64),
    Building(id="research-center", name="Research Center", building_type="Labs", area_sq_ft=61200, current_load_kw=149, load_percent=58),
]


def list_buildings() -> list[Building]:
    return BUILDINGS


def campus_snapshot() -> dict[str, float | str]:
    return {"energy_used_kwh": 847, "energy_cost": 124.80, "carbon_avoided_kg": 426, "peak_demand_kw": 186, "weekly_change_percent": -12.4}
