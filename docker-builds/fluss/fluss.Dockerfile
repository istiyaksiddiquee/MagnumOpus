FROM apache/fluss:0.9.1-incubating
SHELL ["/bin/bash", "-c"]

# --- Build-time jar version pins ---
# VERIFY all of these against Fluss 0.9.1-incubating / Iceberg 1.9.x compatibility
# before building. Carried over from a working 0.8.0-incubating setup as a strong
# starting point -- not yet confirmed correct for 0.9.1.
ARG ICEBERG_AWS_BUNDLE_JAR=iceberg-aws-bundle-1.10.1.jar
ARG ICEBERG_AWS_JAR=iceberg-aws-1.10.1.jar
ARG FAILSAFE_JAR=failsafe-3.3.2.jar
ARG HADOOP_SHADED_JAR=hadoop-apache-3.3.5-2.jar
ARG ICEBERG_HIVE_METASTORE_JAR=iceberg-hive-metastore-1.10.1.jar

ENV FLUSS_HOME=/opt/fluss
ENV HADOOP_CONF_DIR=/opt/fluss/conf

# Coordinator/tablet servers need these to initialize the Iceberg (Hive) catalog
# connection at startup, since datalake.format: iceberg is configured from boot --
# this is required for the base cluster to come up cleanly, independent of
# whether the tiering job itself is running yet.
RUN mkdir -p ${FLUSS_HOME}/plugins/iceberg

COPY stage/${HADOOP_SHADED_JAR}         ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${ICEBERG_AWS_BUNDLE_JAR}    ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${ICEBERG_AWS_JAR}           ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${FAILSAFE_JAR}              ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${ICEBERG_HIVE_METASTORE_JAR} ${FLUSS_HOME}/plugins/iceberg/

# Hive Metastore Thrift client (hive-metastore:3.1.3 to match the hive-metastore
# container in docker-compose) + its resolved transitive deps -- libthrift,
# libfb303, hive-common, etc. Generated via resolve-hive/pom.xml +
# `mvn dependency:copy-dependencies` into stage/hive-metastore-libs/.
# HiveCatalog needs these at runtime (org.apache.hadoop.hive.metastore.api.*),
# not just iceberg-hive-metastore.jar, which only holds Iceberg's own glue code.
COPY stage/hive-metastore-libs/ ${FLUSS_HOME}/plugins/iceberg/

# Fail the build loudly if the resolver step was skipped or produced nothing --
# an empty/missing stage/hive-metastore-libs/ otherwise copies in silently and
# only shows up later as a runtime NoClassDefFoundError.
RUN test -n "$(ls -A ${FLUSS_HOME}/plugins/iceberg/hive-metastore*.jar 2>/dev/null)" \
    || (echo "ERROR: hive-metastore client jar missing from plugins/iceberg/ -- run resolve-hive/pom.xml's mvn dependency:copy-dependencies into stage/hive-metastore-libs/ first" >&2 && exit 1)


# Hadoop-style S3 config -- the Hive/Iceberg catalog path uses Hadoop's
# S3AFileSystem, which reads its own core-site.xml, separate from the
# s3.* keys already set in FLUSS_PROPERTIES.
RUN mkdir -p ${HADOOP_CONF_DIR}
COPY conf/core-site.xml ${HADOOP_CONF_DIR}/core-site.xml

RUN chown -R fluss:fluss ${FLUSS_HOME}

USER fluss:fluss