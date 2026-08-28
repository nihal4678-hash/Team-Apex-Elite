from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Database path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "ecomind.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-add missing columns to existing SQLite tables if needed
    inspector = inspect(engine)
    with engine.connect() as conn:
        # Check simulation_scenario_runs table
        if inspector.has_table("simulation_scenario_runs"):
            cols = [c["name"] for c in inspector.get_columns("simulation_scenario_runs")]
            new_cols = {
                "status": "VARCHAR DEFAULT 'completed'",
                "cancel_requested": "BOOLEAN DEFAULT 0",
                "simulation_start_datetime": "VARCHAR",
                "simulation_end_datetime": "VARCHAR",
                "after_hours_monitoring": "BOOLEAN DEFAULT 1",
                "total_hourly_records": "INTEGER DEFAULT 0",
                "completed_hourly_records": "INTEGER DEFAULT 0",
                "generated_records_count": "INTEGER DEFAULT 0",
                "alerts_detected_count": "INTEGER DEFAULT 0",
                "current_timestamp": "VARCHAR",
                "current_building_id": "VARCHAR",
                "started_at": "VARCHAR",
                "stopped_at": "VARCHAR",
                "completed_at": "VARCHAR",
                "failure_message": "TEXT"
            }
            for col_name, col_type in new_cols.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f"ALTER TABLE simulation_scenario_runs ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        pass

        # Check alerts table
        if inspector.has_table("alerts"):
            cols = [c["name"] for c in inspector.get_columns("alerts")]
            if "scenario_id" not in cols:
                try:
                    conn.execute(text("ALTER TABLE alerts ADD COLUMN scenario_id VARCHAR"))
                    conn.commit()
                except Exception:
                    pass
            if "data_source" not in cols:
                try:
                    conn.execute(text("ALTER TABLE alerts ADD COLUMN data_source VARCHAR DEFAULT 'actual'"))
                    conn.commit()
                except Exception:
                    pass
