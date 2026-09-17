FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY app.py .
COPY lin_reg.bin .

CMD ["python", "app.py"]