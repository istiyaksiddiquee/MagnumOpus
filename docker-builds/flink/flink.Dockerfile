FROM flink:1.20-java11
SHELL ["/bin/bash", "-c"]

ENV HADOOP_CONF_DIR=/opt/flink/conf

# --- Core Fluss <-> Flink connectivity ---
COPY lib/fluss-flink-1.20-0.9.1-incubating.jar   ${FLINK_HOME}/lib/
COPY lib/fluss-lake-iceberg-0.9.1-incubating.jar ${FLINK_HOME}/lib/

# --- Iceberg 1.9.1: the version Fluss 0.9.1 was built against.
#     1.10.x is unusable here: iceberg-parquet 1.10.x needs Parquet >= 1.16 for
#     VariantLogicalTypeAnnotation, but 1.16 changed the Types$PrimitiveBuilder.as()
#     signature it was compiled against. 1.9.1 predates variant entirely. ---
COPY lib/iceberg-api-1.9.1.jar             ${FLINK_HOME}/lib/
COPY lib/iceberg-common-1.9.1.jar          ${FLINK_HOME}/lib/
COPY lib/iceberg-core-1.9.1.jar            ${FLINK_HOME}/lib/
COPY lib/iceberg-bundled-guava-1.9.1.jar   ${FLINK_HOME}/lib/
COPY lib/iceberg-data-1.9.1.jar            ${FLINK_HOME}/lib/
COPY lib/iceberg-parquet-1.9.1.jar         ${FLINK_HOME}/lib/
COPY lib/iceberg-hive-metastore-1.9.1.jar  ${FLINK_HOME}/lib/
COPY lib/iceberg-aws-1.9.1.jar             ${FLINK_HOME}/lib/
COPY lib/iceberg-aws-bundle-1.9.1.jar      ${FLINK_HOME}/lib/
COPY lib/failsafe-3.3.2.jar                ${FLINK_HOME}/lib/

# --- Parquet 1.15.2 + Avro (matches Iceberg 1.9.1's compiled-against API) ---
COPY lib/parquet-column-1.15.2.jar            ${FLINK_HOME}/lib/
COPY lib/parquet-hadoop-1.15.2.jar            ${FLINK_HOME}/lib/
COPY lib/parquet-common-1.15.2.jar            ${FLINK_HOME}/lib/
COPY lib/parquet-format-structures-1.15.2.jar ${FLINK_HOME}/lib/
COPY lib/parquet-avro-1.15.2.jar              ${FLINK_HOME}/lib/
COPY lib/parquet-encoding-1.15.2.jar          ${FLINK_HOME}/lib/
COPY lib/parquet-jackson-1.15.2.jar           ${FLINK_HOME}/lib/
COPY lib/avro-1.12.0.jar                      ${FLINK_HOME}/lib/

# --- Hive Metastore client + Hadoop + Jackson (not Iceberg-versioned) ---
COPY lib/hive-exec-2.3.10.jar             ${FLINK_HOME}/lib/
COPY lib/hadoop-client-api-3.3.6.jar      ${FLINK_HOME}/lib/
COPY lib/hadoop-client-runtime-3.3.6.jar  ${FLINK_HOME}/lib/
COPY lib/commons-logging-1.2.jar          ${FLINK_HOME}/lib/
COPY lib/jackson-core-2.15.2.jar          ${FLINK_HOME}/lib/
COPY lib/jackson-databind-2.15.2.jar      ${FLINK_HOME}/lib/
COPY lib/jackson-annotations-2.15.2.jar   ${FLINK_HOME}/lib/

# Same Hadoop S3A config the Fluss server uses, for consistent MinIO access
COPY core-site.xml ${HADOOP_CONF_DIR}/core-site.xml

# The tiering job itself -- submitted via `flink run`, not placed in lib/
COPY lib/fluss-flink-tiering-0.9.1-incubating.jar /opt/flink/usrlib/fluss-flink-tiering-0.9.1-incubating.jar

# fluss-lake-iceberg's own bundled org/apache/iceberg/* classes shadow the
# matched set above on Flink's flat classpath. Strip them.
RUN apt-get update && apt-get install -y --no-install-recommends zip \
    && zip -d ${FLINK_HOME}/lib/fluss-lake-iceberg-0.9.1-incubating.jar 'org/apache/iceberg/*' \
    && zip -d ${FLINK_HOME}/lib/hive-exec-2.3.10.jar 'org/apache/parquet/*' \
    && apt-get purge -y zip && rm -rf /var/lib/apt/lists/*