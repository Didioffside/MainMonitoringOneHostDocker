FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y tshark iproute2 tcpdump docker.io cron

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

CMD ["python", "main.py"]