# import asyncio
# import time

# import fluss
# import pyarrow as pa

# BOOTSTRAP_SERVERS = "coordinator-server:9123"
# DATABASE = "magnum_opus"
# TABLE_NAME = "tlc_landing"

# # TODO: replace with your actual NYC TLC field set / types.
# SCHEMA = fluss.Schema(
#     pa.schema(
#         [

#             "": Column(Float64, coerce=True),
#                 "lpep_pickup_datetime": Column(datetime64),
#                 "lpep_dropoff_datetime": Column(datetime64),
#                 "store_and_fwd_flag": Column(object, nullable=True),
#                 "RatecodeID": Column(Float64, nullable=True, coerce=True),
#                 "PULocationID": Column(Float64, coerce=True),
#                 "DOLocationID": Column(Float64, coerce=True),
#                 "passenger_count": Column(Float64, coerce=True, nullable=True),
#                 "trip_distance": Column(Float64, coerce=True),
#                 "fare_amount": Column(Float64, coerce=True),
#                 "extra": Column(Float64, coerce=True),
#                 "mta_tax": Column(Float64, coerce=True),
#                 "tip_amount": Column(Float64, coerce=True),
#                 "tolls_amount": Column(Float64, coerce=True),
#                 "ehail_fee": Column(Float64, coerce=True, nullable=True),
#                 "improvement_surcharge": Column(Float64, coerce=True),
#                 "total_amount": Column(Float64, coerce=True),
#                 "payment_type": Column(Float64, coerce=True, nullable=True),
#                 "trip_type": Column(Float64, coerce=True, nullable=True),
#                 "congestion_surcharge": Column(Float64, coerce=True, nullable=True),
#                 "cbd_congestion_fee": Column(Float64, coerce=True, nullable=True),


#             pa.field("VendorID", pa.int64()),
#             pa.field("lpep_pickup_datetime", pa.timestamp("us")),
#             pa.field("lpep_dropoff_datetime", pa.timestamp("us")),
#             pa.field("store_and_fwd_flag", pa.timestamp("us")),

#             pa.field("dropoff_datetime", pa.timestamp("us")),
#             pa.field("pu_location_id", pa.int32()),
#             pa.field("do_location_id", pa.int32()),
#             pa.field("trip_distance", pa.float64()),
#             pa.field("fare_amount", pa.float64()),
#             pa.field("ingestion_month", pa.string()),
#             pa.field("ingested_at", pa.timestamp("us")),
#         ]
#     )
# )


# async def wait_for_cluster(retries: int = 20, delay_seconds: int = 5) -> fluss.Connection:
#     last_error = None
#     for attempt in range(1, retries + 1):
#         try:
#             conn = await fluss.connect(bootstrap_servers=BOOTSTRAP_SERVERS)
#             await conn.get_admin().list_databases()
#             print(f"Connected to Fluss cluster on attempt {attempt}")
#             return conn
#         except Exception as exc:  # noqa: BLE001 - broad on purpose for a retry loop
#             last_error = exc
#             print(f"Attempt {attempt}/{retries}: cluster not ready yet ({exc})")
#             time.sleep(delay_seconds)
#     raise RuntimeError(f"Fluss cluster never became reachable: {last_error}")


# async def main() -> None:
#     conn = await wait_for_cluster()
#     admin = conn.get_admin()

#     await admin.create_database(DATABASE, ignore_if_exists=True)

#     table_path = fluss.TablePath(DATABASE, TABLE_NAME)
#     descriptor = fluss.TableDescriptor(SCHEMA)  # no primary_keys -> Log table

#     await admin.create_table(table_path, descriptor, ignore_if_exists=True)
#     print(f"Ensured table exists: {DATABASE}.{TABLE_NAME}")


# if __name__ == "__main__":
#     asyncio.run(main())
