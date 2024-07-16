#!/bin/bash
set -e

# Wait for the InfluxDB service to be up and running
echo "Waiting for InfluxDB to be available..."
until curl -sl -I http://localhost:8086/health | grep "200 OK" > /dev/null; do
    echo "InfluxDB not available yet..."
    sleep 5
done

echo "InfluxDB is up. Creating additional buckets..."

# Create additional buckets. Adjust the names and retention policies as needed.
influx bucket create --name "Final" --retention 0 --org MyOrg --token InfluxDBToken
influx bucket create --name "Final_Node" --retention 0 --org MyOrg --token InfluxDBToken
influx bucket create --name "Network" --retention 0 --org MyOrg --token InfluxDBToken

echo "Additional buckets created successfully."
