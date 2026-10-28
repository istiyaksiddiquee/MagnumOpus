import asyncio
import json
import os

import fluss
import pulsar

FLUSS_BOOTSTRAP_SERVERS = os.environ["FLUSS_BOOTSTRAP_SERVERS"]
FLUSS_DATABASE = os.environ["FLUSS_DATABASE"]
FLUSS_TABLE = os.environ["FLUSS_TABLE"]
PULSAR_SERVICE_URL = os.environ["PULSAR_SERVICE_URL"]
PULSAR_TOPIC = os.environ["PULSAR_TOPIC"]
OFFSET_STATE_PATH = os.environ["OFFSET_STATE_PATH"]

POLL_TIMEOUT_MS = 5000


def load_offsets() -> dict[int, int]:
    if os.path.exists(OFFSET_STATE_PATH):
        with open(OFFSET_STATE_PATH) as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}


def save_offsets(offsets: dict[int, int]) -> None:
    tmp_path = OFFSET_STATE_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(offsets, f)
    os.replace(tmp_path, OFFSET_STATE_PATH)


async def run() -> None:
    config = fluss.Config({"bootstrap.servers": FLUSS_BOOTSTRAP_SERVERS})
    conn = await fluss.FlussConnection.create(config)
    table_path = fluss.TablePath(FLUSS_DATABASE, FLUSS_TABLE)
    table = await conn.get_table(table_path)
    admin = conn.get_admin()
    table_info = await admin.get_table_info(table_path)
    num_buckets = table_info.num_buckets

    # Resume from last committed offset per bucket if we've run before,
    # otherwise start from the earliest record (streams the full existing
    # table on first run, then tails new writes from then on).
    offsets = load_offsets()

    scan = table.new_scan()
    scanner = await scan.create_log_scanner()

    for bucket_id in range(num_buckets):
        start_offset = offsets.get(bucket_id, fluss.EARLIEST_OFFSET)
        scanner.subscribe(bucket_id=bucket_id, start_offset=start_offset)

    pulsar_client = pulsar.Client(PULSAR_SERVICE_URL)
    producer = pulsar_client.create_producer(PULSAR_TOPIC)

    print(
        f"Producer started. Tailing {FLUSS_DATABASE}.{FLUSS_TABLE} " f"-> Pulsar topic '{PULSAR_TOPIC}' ({num_buckets} bucket(s))",
        flush=True,
    )

    try:
        while True:
            records = scanner.poll(timeout_ms=POLL_TIMEOUT_MS)
            if records.is_empty():
                continue

            sent = 0
            for bucket, bucket_records in records.items():
                for record in bucket_records:
                    # default=str handles datetime/Decimal-like values from
                    # the row dict so json.dumps doesn't choke on them.
                    payload = json.dumps(record.row, default=str).encode("utf-8")
                    producer.send(payload)
                    offsets[bucket.bucket_id] = record.offset + 1
                    sent += 1

            if sent:
                save_offsets(offsets)
                print(f"Sent {sent} record(s) to Pulsar", flush=True)
    finally:
        producer.close()
        pulsar_client.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(run())
