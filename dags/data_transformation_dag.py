import asyncio
import subprocess
from datetime import datetime

import pandas as pd
import pyarrow as pa

from airflow.decorators import dag, task

# --- Edit these to match your actual paths/hosts ---
BRONZE_PROJECT_DIR = "/opt/airflow/dbt-transform/bronze"
SILVER_PROJECT_DIR = "/opt/airflow/dbt-transform/silver"
GOLD_PROJECT_DIR = "/opt/airflow/dbt-transform/gold"
PROFILES_DIR = "/opt/airflow/dbt-transform/"

TRINO_HOST = "trino"
TRINO_PORT = 8000
TRINO_USER = "airflow"
TRINO_CATALOG = "iceberg"
GOLD_SCHEMA = "gold"
GOLD_TABLE = "trip_events_stream"

FLUSS_BOOTSTRAP_SERVERS = "coordinator-server:9123"
FLUSS_DATABASE = "lakehouse_db"
FLUSS_TABLE = "trip_events_stream"
# ----------------------------------------------------

# Column types must match the actual gold table (from `DESCRIBE`), expressed
# as PyArrow types for the Fluss schema.
FLUSS_COLUMNS: list[tuple[str, pa.DataType]] = [
    ("trip_id", pa.string()),
    ("pickup_datetime", pa.timestamp("us")),
    ("dropoff_datetime", pa.timestamp("us")),
    ("trip_duration_minutes", pa.int64()),
    ("pickup_locationid", pa.int64()),
    ("pickup_borough", pa.string()),
    ("pickup_zone", pa.string()),
    ("dropoff_locationid", pa.int64()),
    ("dropoff_borough", pa.string()),
    ("dropoff_zone", pa.string()),
    ("passenger_count", pa.int64()),
    ("fare_amount", pa.float64()),
    ("tip_amount", pa.float64()),
    ("total_amount", pa.float64()),
]


def _run_dbt(project_dir: str, *dbt_args: str) -> None:
    cmd = ["dbt", *dbt_args, "--project-dir", project_dir, "--profiles-dir", PROFILES_DIR]
    subprocess.run(cmd, check=True)


def _read_gold_as_dataframe() -> pd.DataFrame:
    import trino

    conn = trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog=TRINO_CATALOG,
        schema=GOLD_SCHEMA,
    )
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {GOLD_TABLE}")
    rows = cur.fetchall()
    columns = [c[0] for c in cur.description]
    return pd.DataFrame(rows, columns=columns)


async def _write_to_fluss(df: pd.DataFrame) -> int:
    import fluss

    config = fluss.Config({"bootstrap.servers": FLUSS_BOOTSTRAP_SERVERS})
    conn = await fluss.FlussConnection.create(config)
    try:
        admin = conn.get_admin()

        await admin.create_database(FLUSS_DATABASE, ignore_if_exists=True)

        schema = fluss.Schema(pa.schema(FLUSS_COLUMNS))  # no primary_keys -> log table
        descriptor = fluss.TableDescriptor(schema)
        table_path = fluss.TablePath(FLUSS_DATABASE, FLUSS_TABLE)
        await admin.create_table(table_path, descriptor, ignore_if_exists=True)

        table = await conn.get_table(table_path)
        writer = table.new_append().create_writer()
        writer.write_pandas(df)
        await writer.flush()
        return len(df)
    finally:
        conn.close()


@dag(
    dag_id="gold_to_fluss_pipeline",
    description="Bronze -> Silver -> Gold dbt runs, then Gold -> Fluss transfer in pure Python",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["magnum-opus", "medallion", "fluss"],
)
def gold_to_fluss_pipeline():

    @task
    def run_bronze_dbt() -> str:
        _run_dbt(BRONZE_PROJECT_DIR, "run")
        return "bronze_done"

    @task
    def seed_silver_dbt(_upstream: str) -> str:
        _run_dbt(SILVER_PROJECT_DIR, "seed")
        return "silver_seeded"

    @task
    def run_silver_dbt(_upstream: str) -> str:
        _run_dbt(SILVER_PROJECT_DIR, "run")
        return "silver_done"

    @task
    def run_gold_dbt(_upstream: str) -> str:
        _run_dbt(GOLD_PROJECT_DIR, "run")
        return "gold_done"

    @task
    def gold_to_fluss(_upstream: str) -> int:
        df = _read_gold_as_dataframe()
        written = asyncio.run(_write_to_fluss(df))
        return written

    bronze_result = run_bronze_dbt()
    silver_seeded = seed_silver_dbt(bronze_result)
    silver_result = run_silver_dbt(silver_seeded)
    gold_result = run_gold_dbt(silver_result)
    gold_to_fluss(gold_result)


gold_to_fluss_pipeline()
