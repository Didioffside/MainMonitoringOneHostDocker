#!/bin/bash

# Start Sysdig in the background and write output to a file
sysdig -pc -w /src/sysdig_output.scap &

# Get the PID of the sysdig process
SYSDIG_PID=$!

# Run the Python script to forward data to InfluxDB
python3 /src/forward_to_influxdb.py &

# Wait for the sysdig process to finish
wait $SYSDIG_PID
