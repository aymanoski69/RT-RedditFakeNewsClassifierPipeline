FROM apache/airflow:2.9.1-python3.10

USER root

# Install Java 17 instead of 11
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:$PATH"

USER airflow

# Copy and install Python requirements
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt
