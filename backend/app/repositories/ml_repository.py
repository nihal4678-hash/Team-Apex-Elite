from app.repositories.db_repository import db_repository


class MLDataRepository:
    @staticmethod
    def get_buildings() -> list[dict]:
        return db_repository.get_buildings()

    @staticmethod
    def get_snapshot() -> dict:
        return db_repository.get_snapshot()

    @staticmethod
    def get_forecast() -> dict:
        return db_repository.get_forecast()

    @staticmethod
    def get_alerts() -> list[dict]:
        return db_repository.get_alerts()

    @staticmethod
    def get_recommendations() -> list[dict]:
        return db_repository.get_recommendations()

    @staticmethod
    def apply_action(action_id: str, params: dict = None) -> dict:
        return db_repository.apply_action(action_id, params)

    @staticmethod
    def resolve_alert(alert_id: str) -> dict:
        return db_repository.resolve_alert(alert_id)

    @staticmethod
    def run_simulation(building_id: str, temp_delta: float, duration_minutes: int) -> dict:
        return db_repository.run_simulation(building_id, temp_delta, duration_minutes)

    @staticmethod
    def get_sustainability_data() -> dict:
        return db_repository.get_sustainability_data()


ml_repository = MLDataRepository()
