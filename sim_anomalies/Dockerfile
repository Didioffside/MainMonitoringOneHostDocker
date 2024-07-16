FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y stress iptables iproute2 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

CMD ["python", "app.py"]