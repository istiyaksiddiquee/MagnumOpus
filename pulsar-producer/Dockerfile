FROM python:3.11-slim

WORKDIR /app

# Pin pyfluss to the version confirmed compatible with Fluss server 0.9.1-incubating.
RUN pip install --no-cache-dir pyfluss==0.1.0 pulsar-client

COPY producer.py .

CMD ["python", "producer.py"]