FROM apache/fluss:0.9.1-incubating
SHELL ["/bin/bash", "-c"]

# --- Build-time jar version pins ---
# VERIFY all of these against Fluss 0.9.1-incubating / Iceberg 1.9.x compatibility
# before building. Carried over from a working 0.8.0-incubating setup as a strong
# starting point -- not yet confirmed correct for 0.9.1.
ARG HADOOP_SHADED_JAR=hadoop-apache-3.3.5-3.jar
ARG ICEBERG_CORE_JAR=iceberg-core-1.9.1.jar
ARG ICEBERG_AWS_BUNDLE_JAR=iceberg-aws-bundle-1.9.1.jar
ARG ICEBERG_AWS_JAR=iceberg-aws-1.9.1.jar
ARG AWS_SDK_BUNDLE_JAR=aws-java-sdk-bundle-1.12.262.jar
ARG HADOOP_SHADED_GUAVA_JAR=hadoop-shaded-guava-1.1.1.jar

ENV FLUSS_HOME=/opt/fluss
ENV HADOOP_CONF_DIR=/opt/fluss/conf

# Coordinator/tablet servers need these to initialize the Iceberg (Hive) catalog
# connection at startup, since datalake.format: iceberg is configured from boot --
# this is required for the base cluster to come up cleanly, independent of
# whether the tiering job itself is running yet.
RUN mkdir -p ${FLUSS_HOME}/plugins/iceberg

COPY stage/${HADOOP_SHADED_JAR}        ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${ICEBERG_CORE_JAR}         ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${ICEBERG_AWS_BUNDLE_JAR}   ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${ICEBERG_AWS_JAR}          ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${AWS_SDK_BUNDLE_JAR}       ${FLUSS_HOME}/plugins/iceberg/
COPY stage/${HADOOP_SHADED_GUAVA_JAR}  ${FLUSS_HOME}/plugins/iceberg/

# Hadoop-style S3 config -- the Hive/Iceberg catalog path uses Hadoop's
# S3AFileSystem, which reads its own core-site.xml, separate from the
# s3.* keys already set in FLUSS_PROPERTIES.
RUN mkdir -p ${HADOOP_CONF_DIR}
COPY conf/core-site.xml ${HADOOP_CONF_DIR}/core-site.xml

RUN chown -R fluss:fluss ${FLUSS_HOME}

USER fluss:fluss