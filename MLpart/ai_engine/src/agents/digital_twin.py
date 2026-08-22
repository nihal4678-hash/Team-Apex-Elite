"""Stage 1 — Campus digital twin for Vignan University, Vadlamudi."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.config import CAMPUS, GENERATED_DIR, RANDOM_SEED
from src.utils.io import save_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.digital_twin")

# Building archetypes inspired by VFSTR Vadlamudi campus layout (2024-25 Carbon Audit Grounding).
BUILDING_SPECS: list[dict[str, Any]] = [
    {
        "building_id": "BLK-A",
        "name": "Academic Block A — Engineering",
        "category": "academic",
        "area_sqm": 14030.25,
        "solar_pv": True,
        "floors": 4,
        "has_hvac": True,
        "rooms_per_floor": 4,
        "room_prefix": "classroom",
        "capacity_range": (40, 70),
        "computers_range": (0, 2),
        "lights_per_seat": 0.35,
        "fans_per_seat": 0.18,
        "projectors": True,
    },
    {
        "building_id": "BLK-B",
        "name": "Academic Block B — Sciences",
        "category": "academic",
        "area_sqm": 10490.70,
        "solar_pv": True,
        "floors": 4,
        "has_hvac": True,
        "rooms_per_floor": 3,
        "room_prefix": "classroom",
        "capacity_range": (35, 60),
        "computers_range": (0, 4),
        "lights_per_seat": 0.35,
        "fans_per_seat": 0.18,
        "projectors": True,
    },
    {
        "building_id": "BLK-C",
        "name": "Academic Block C — Management & Humanities",
        "category": "academic",
        "area_sqm": 9936.96,
        "solar_pv": True,
        "floors": 3,
        "has_hvac": True,
        "rooms_per_floor": 3,
        "room_prefix": "classroom",
        "capacity_range": (40, 80),
        "computers_range": (0, 2),
        "lights_per_seat": 0.32,
        "fans_per_seat": 0.16,
        "projectors": True,
    },
    {
        "building_id": "LAB-CSE",
        "name": "Computer Science Laboratories (Building E)",
        "category": "computer_lab",
        "area_sqm": 6943.33,
        "solar_pv": False,
        "floors": 3,
        "has_hvac": True,
        "rooms_per_floor": 3,
        "room_prefix": "lab",
        "capacity_range": (40, 70),
        "computers_range": (40, 72),
        "lights_per_seat": 0.4,
        "fans_per_seat": 0.12,
        "projectors": True,
    },
    {
        "building_id": "LIB",
        "name": "Central Library (Building F)",
        "category": "library",
        "area_sqm": 4722.08,
        "solar_pv": False,
        "floors": 3,
        "has_hvac": True,
        "rooms_per_floor": 2,
        "room_prefix": "reading_hall",
        "capacity_range": (80, 160),
        "computers_range": (12, 40),
        "lights_per_seat": 0.28,
        "fans_per_seat": 0.14,
        "projectors": False,
    },
    {
        "building_id": "HST-B",
        "name": "Boys Hostel — Vignan Vihar (Building I)",
        "category": "hostel",
        "area_sqm": 12889.91,
        "solar_pv": True,
        "floors": 4,
        "has_hvac": False,
        "rooms_per_floor": 4,
        "room_prefix": "wing",
        "capacity_range": (36, 52),
        "computers_range": (0, 4),
        "lights_per_seat": 0.22,
        "fans_per_seat": 0.22,
        "projectors": False,
    },
    {
        "building_id": "HST-G",
        "name": "Girls Hostel — Priyadarshini Block (Building H)",
        "category": "hostel",
        "area_sqm": 10747.75,
        "solar_pv": True,
        "floors": 4,
        "has_hvac": False,
        "rooms_per_floor": 4,
        "room_prefix": "wing",
        "capacity_range": (32, 48),
        "computers_range": (0, 3),
        "lights_per_seat": 0.22,
        "fans_per_seat": 0.22,
        "projectors": False,
    },
    {
        "building_id": "ADM",
        "name": "Administrative Block (Building G)",
        "category": "admin",
        "area_sqm": 2694.82,
        "solar_pv": True,
        "floors": 3,
        "has_hvac": True,
        "rooms_per_floor": 3,
        "room_prefix": "office",
        "capacity_range": (8, 24),
        "computers_range": (6, 18),
        "lights_per_seat": 0.5,
        "fans_per_seat": 0.2,
        "projectors": False,
    },
    {
        "building_id": "CAF",
        "name": "Central Complex & Cafeteria (Building D)",
        "category": "cafeteria",
        "area_sqm": 39460.53,
        "solar_pv": True,
        "floors": 2,
        "has_hvac": True,
        "rooms_per_floor": 2,
        "room_prefix": "dining",
        "capacity_range": (80, 140),
        "computers_range": (0, 2),
        "lights_per_seat": 0.2,
        "fans_per_seat": 0.15,
        "projectors": False,
    },
]


def _clamp_int(value: float, lo: int = 0) -> int:
    return max(lo, int(round(value)))


def generate_digital_twin(seed: int = RANDOM_SEED) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    buildings_rows: list[dict[str, Any]] = []
    rooms_rows: list[dict[str, Any]] = []
    devices_rows: list[dict[str, Any]] = []

    for spec in BUILDING_SPECS:
        n_rooms = spec["floors"] * spec["rooms_per_floor"]
        buildings_rows.append(
            {
                "building_id": spec["building_id"],
                "building_name": spec["name"],
                "category": spec["category"],
                "area_sqm": spec["area_sqm"],
                "solar_pv_installed": spec["solar_pv"],
                "floors": spec["floors"],
                "room_count": n_rooms,
                "hvac_available": spec["has_hvac"],
                "campus": CAMPUS["name"],
                "latitude": CAMPUS["latitude"],
                "longitude": CAMPUS["longitude"],
            }
        )
        for floor in range(1, spec["floors"] + 1):
            for idx in range(1, spec["rooms_per_floor"] + 1):
                room_id = f"{spec['building_id']}-F{floor:02d}-R{idx:02d}"
                capacity = int(rng.integers(*spec["capacity_range"]))
                n_computers = int(rng.integers(*spec["computers_range"])) if spec["computers_range"][1] > 0 else 0
                n_lights = max(6, _clamp_int(capacity * spec["lights_per_seat"]))
                n_fans = max(2, _clamp_int(capacity * spec["fans_per_seat"]))
                n_ac = (2 if spec["has_hvac"] and capacity >= 50 else 1) if spec["has_hvac"] else 0
                n_projectors = 1 if spec["projectors"] else 0
                rooms_rows.append(
                    {
                        "room_id": room_id,
                        "building_id": spec["building_id"],
                        "building_name": spec["name"],
                        "category": spec["category"],
                        "floor": floor,
                        "room_name": f"{spec['room_prefix'].replace('_', ' ').title()} {floor}{idx:02d}",
                        "room_type": spec["room_prefix"],
                        "capacity": capacity,
                        "hvac_available": spec["has_hvac"],
                        "computer_count": n_computers,
                        "lighting_count": n_lights,
                        "fan_count": n_fans,
                        "ac_count": n_ac,
                        "projector_count": n_projectors,
                    }
                )
                inventory = {
                    "light": n_lights,
                    "fan": n_fans,
                    "ac": n_ac,
                    "computer": n_computers,
                    "projector": n_projectors,
                }
                for device_type, count in inventory.items():
                    if count <= 0:
                        continue
                    devices_rows.append(
                        {
                            "device_id": f"{room_id}-{device_type.upper()}",
                            "room_id": room_id,
                            "building_id": spec["building_id"],
                            "device_type": device_type,
                            "count": count,
                            "rated_watts_each": {
                                "light": 28.0,
                                "fan": 75.0,
                                "ac": 1650.0,
                                "computer": 180.0,
                                "projector": 260.0,
                            }[device_type],
                            "controllable": True,
                        }
                    )

    buildings = pd.DataFrame(buildings_rows)
    rooms = pd.DataFrame(rooms_rows)
    devices = pd.DataFrame(devices_rows)
    metadata = {
        "campus": CAMPUS,
        "building_count": int(len(buildings)),
        "room_count": int(len(rooms)),
        "device_sku_count": int(len(devices)),
        "total_capacity": int(rooms["capacity"].sum()),
        "categories": sorted(buildings["category"].unique().tolist()),
        "generator": "stage1_digital_twin",
        "seed": seed,
    }
    return {"buildings": buildings, "rooms": rooms, "devices": devices, "metadata": metadata}


def validate_digital_twin(
    buildings: pd.DataFrame, rooms: pd.DataFrame, devices: pd.DataFrame
) -> ValidationResult:
    result = ValidationResult(stage="stage1_digital_twin", passed=True)
    result.add("unique_building_ids", buildings["building_id"].is_unique, f"n={len(buildings)}")
    result.add(
        "rooms_belong_to_buildings",
        rooms["building_id"].isin(buildings["building_id"]).all(),
        "orphan rooms" if not rooms["building_id"].isin(buildings["building_id"]).all() else "ok",
    )
    result.add("unique_room_ids", rooms["room_id"].is_unique, f"n={len(rooms)}")
    result.add(
        "realistic_capacity",
        bool((rooms["capacity"].between(6, 200)).all()),
        f"min={rooms['capacity'].min()} max={rooms['capacity'].max()}",
    )
    result.add(
        "devices_belong_to_rooms",
        devices["room_id"].isin(rooms["room_id"]).all(),
        "ok" if devices["room_id"].isin(rooms["room_id"]).all() else "orphan devices",
    )
    required_categories = {"academic", "computer_lab", "library", "hostel", "admin", "cafeteria"}
    present = set(buildings["category"].unique())
    result.add("required_building_types", required_categories.issubset(present), f"present={sorted(present)}")
    return result


def persist_digital_twin(artifacts: dict[str, Any]) -> dict[str, str]:
    paths = {
        "buildings": str(save_csv(artifacts["buildings"], GENERATED_DIR / "buildings.csv")),
        "rooms": str(save_csv(artifacts["rooms"], GENERATED_DIR / "rooms.csv")),
        "devices": str(save_csv(artifacts["devices"], GENERATED_DIR / "devices.csv")),
        "campus_metadata": str(save_json(GENERATED_DIR / "campus_metadata.json", artifacts["metadata"])),
    }
    logger.info("Digital twin written to %s", GENERATED_DIR)
    return paths


def run_stage1() -> dict[str, Any]:
    artifacts = generate_digital_twin()
    validation = validate_digital_twin(artifacts["buildings"], artifacts["rooms"], artifacts["devices"])
    paths = persist_digital_twin(artifacts)
    report = {
        "stage": 1,
        "name": "Campus Digital Twin Generator",
        "validation": validation.to_dict(),
        "paths": paths,
        "summary": {
            "buildings": int(len(artifacts["buildings"])),
            "rooms": int(len(artifacts["rooms"])),
            "device_skus": int(len(artifacts["devices"])),
            "total_capacity": int(artifacts["rooms"]["capacity"].sum()),
        },
        "pending_issues": validation.pending_issues,
    }
    save_json(GENERATED_DIR.parent.parent / "reports" / "stage1_digital_twin.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 1 validation failed: {validation.pending_issues}")
    return report
