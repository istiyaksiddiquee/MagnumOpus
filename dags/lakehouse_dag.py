from datetime import datetime
from airflow.sdk import dag, task
from pendulum import duration
import os
from pathlib import Path

DATA_DIR = Path("/opt/airflow/shared_data")
DATA_DIR.mkdir(exist_ok=True)


@dag(
    dag_id="lakehouse_taxi",
    schedule="0 6 2 * *",
    start_date=datetime(2025, 1, 1),  # Before Jan 2025
    end_date=datetime(2025, 10, 15),
    default_args={"retries": 1, "retry_delay": duration(minutes=1)},
    max_active_runs=2,
    catchup=True,
)
def lakehouse_dag():

    @task()
    def scrape_data_from_source(**context):
        import pandas as pd
        from urllib.error import HTTPError
        from airflow.exceptions import AirflowSkipException
        from datetime import datetime

        logical_date = context["ts"]
        print(f"Logical date for this run: {logical_date}")
        date_obj = datetime.fromisoformat(logical_date)
        month = date_obj.month
        if month < 10:
            month = f"0{month}"

        year_month_duo = f"{date_obj.year}-{month}"

        URL_PREFIX = "https://d37ci6vzurychx.cloudfront.net/trip-data"
        URL_TEMPLATE = f"{URL_PREFIX}/green_tripdata_{year_month_duo}.parquet"

        try:
            df = pd.read_parquet(URL_TEMPLATE)

            print("Parquet file read successfully. Dataframe shape: ", df.shape)
            # Convert to dictionary for XCom serialization
            year_month_duo = f"{date_obj.year}_{month}"
            path = DATA_DIR / f"green_{year_month_duo}.parquet"
            df.to_parquet(path)

        except HTTPError:
            print(f"The requested file is not available: {URL_TEMPLATE}")
            # Skip this task instead of returning None
            raise AirflowSkipException(f"File not available for {year_month_duo}")

        return str(year_month_duo)

    @task()
    def data_validation(year_month_duo: str):
        import pandas as pd
        from numpy import datetime64
        import great_expectations as gx
        import json
        import uuid
        from great_expectations.core import ExpectationSuite
        from pandera.errors import SchemaError
        from pandera import Column, DataFrameSchema, Float64, Index
        from airflow.exceptions import AirflowSkipException

        # Reconstruct DataFrame from dictionary
        path = DATA_DIR / f"green_{year_month_duo}.parquet"
        df = pd.read_parquet(path)

        if df.empty:
            raise AirflowSkipException("Empty dataframe received")

        schema = DataFrameSchema(
            {
                "VendorID": Column(Float64, coerce=True),
                "lpep_pickup_datetime": Column(datetime64),
                "lpep_dropoff_datetime": Column(datetime64),
                "store_and_fwd_flag": Column(object, nullable=True),
                "RatecodeID": Column(Float64, nullable=True, coerce=True),
                "PULocationID": Column(Float64, coerce=True),
                "DOLocationID": Column(Float64, coerce=True),
                "passenger_count": Column(Float64, coerce=True, nullable=True),
                "trip_distance": Column(Float64, coerce=True),
                "fare_amount": Column(Float64, coerce=True),
                "extra": Column(Float64, coerce=True),
                "mta_tax": Column(Float64, coerce=True),
                "tip_amount": Column(Float64, coerce=True),
                "tolls_amount": Column(Float64, coerce=True),
                "ehail_fee": Column(Float64, coerce=True, nullable=True),
                "improvement_surcharge": Column(Float64, coerce=True),
                "total_amount": Column(Float64, coerce=True),
                "payment_type": Column(Float64, coerce=True, nullable=True),
                "trip_type": Column(Float64, coerce=True, nullable=True),
                "congestion_surcharge": Column(Float64, coerce=True, nullable=True),
                "cbd_congestion_fee": Column(Float64, coerce=True, nullable=True),
            },
            index=Index(int),
            strict=True,
        )

        try:
            schema.validate(df)
        except SchemaError as e:
            print(f"Schema validation error: {e}")
            raise AirflowSkipException("Schema validation failed")

        df["lpep_pickup_datetime"] = df["lpep_pickup_datetime"].astype("str")
        df["lpep_dropoff_datetime"] = df["lpep_dropoff_datetime"].astype("str")

        context = gx.get_context(context_root_dir="/opt/airflow/gx/initial_gx")

        print("Available suites:", context.suites.all())

        try:
            datasource = context.data_sources.get("pandas_datasource2")
            print("Using existing datasource")
        except Exception:
            datasource = context.data_sources.add_pandas("pandas_datasource2")
            print("Created new datasource")

        # Get existing asset or create new one
        try:
            taxi_asset = datasource.get_asset("taxi_df")
            print("Using existing asset")
        except Exception:
            taxi_asset = datasource.add_dataframe_asset(name="taxi_df")
            print("Created new asset")

        # Build batch definition - use unique name or get existing
        try:
            batch_definition = taxi_asset.get_batch_definition("batch_def")
        except Exception:
            batch_definition = taxi_asset.add_batch_definition_whole_dataframe("batch_def")

        # Ensure suite is loaded in context
        suite_path = "/opt/airflow/gx/initial_gx/expectations/green_taxi_expectation_suite.json"
        with open(suite_path, "r") as f:
            suite_dict = json.load(f)

        suite = ExpectationSuite(**suite_dict)

        # Force add/update
        try:
            context.suites.delete(suite.name)
        except:
            pass
        context.suites.add(suite)

        # Create validation using suite NAME, not object
        validation_name = f"taxi_validation_{uuid.uuid4().hex[:8]}"

        validation_definition = gx.ValidationDefinition(name=validation_name, data=batch_definition, suite=context.suites.get(suite.name))

        # Add to context
        validation_definition = context.validation_definitions.add(validation_definition)

        validation_result = validation_definition.run(batch_parameters={"dataframe": df})

        print(f"Validation success: {validation_result.success}")

        if not validation_result.success:
            raise AirflowSkipException("Great Expectations validation failed")

        validated_path = DATA_DIR / f"validated_{year_month_duo}.parquet"
        df.to_parquet(validated_path)
        return str(year_month_duo)

    @task()
    def db_injection(year_month_duo: str):
        import pandas as pd
        from ingestion_script import ingest_callable

        from datetime import datetime

        validated_path = DATA_DIR / f"validated_{year_month_duo}.parquet"
        df = pd.read_parquet(validated_path)

        if df.empty:
            print("No data to inject")
            return False

        # Get environment variables
        PG_DATABASE = os.getenv("PG_DATABASE")

        # Format table name with execution date
        table_name = f"green_taxi_{year_month_duo}"

        ingest_callable(PG_DATABASE, table_name, df)

        return str(year_month_duo)

    # Bronze transform - now properly using task output
    @task()
    def run_bronze_transform(year_month_duo: int):
        """Run dbt bronze transformation"""
        import subprocess

        table_name = f"green_taxi_{year_month_duo}"
        cmd = [
            "dbt",
            "run",
            "--vars",
            f"db_name: {table_name}",
            "--project-dir",
            "/opt/airflow/dbt-transform/bronze",
            "--profiles-dir",
            "/opt/airflow/dbt-transform",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            raise Exception(f"dbt bronze run failed: {result.stderr}")

        print(result.stdout)
        return {"status": "success", "step": "bronze"}

    @task()
    def run_silver_transform(bronze_result: dict):
        """Run dbt silver transformation"""
        import subprocess

        cmd = ["dbt", "run", "--project-dir", "/opt/airflow/dbt-transform/silver", "--profiles-dir", "/opt/airflow/dbt-transform"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            raise Exception(f"dbt silver run failed: {result.stderr}")

        print(result.stdout)
        return {"status": "success", "step": "silver"}

    @task()
    def run_gold_transform(silver_result: dict):
        """Run dbt gold transformation"""
        import subprocess

        cmd = ["dbt", "run", "--project-dir", "/opt/airflow/dbt-transform/gold", "--profiles-dir", "/opt/airflow/dbt-transform"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            raise Exception(f"dbt gold run failed: {result.stderr}")

        print(result.stdout)
        return {"status": "success", "step": "gold"}

    year_month_duo = scrape_data_from_source()
    year_month_duo = data_validation(year_month_duo=year_month_duo)
    year_month_duo = db_injection(year_month_duo=year_month_duo)
    # bronze_result = run_bronze_transform(year_month_duo=year_month_duo)
    # silver_result = run_silver_transform(bronze_result)
    # gold_result = run_gold_transform(silver_result)


lakehouse_dag()
