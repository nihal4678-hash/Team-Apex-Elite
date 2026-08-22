from app.repositories.ml_repository import ml_repository
from app.schemas.building import BuildingSchema
from app.schemas.snapshot import SnapshotSchema


def list_buildings() -> list[BuildingSchema]:
    raw_data = ml_repository.get_buildings()
    return [BuildingSchema(**b) for b in raw_data]


def campus_snapshot() -> SnapshotSchema:
    raw_data = ml_repository.get_snapshot()
    return SnapshotSchema(**raw_data)
