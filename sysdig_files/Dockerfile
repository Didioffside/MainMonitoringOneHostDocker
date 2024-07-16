# Stage 1: Use a base image with Python
FROM python:3.8-slim as python-base

# Copy the Python script from the local machine to the build context
COPY forward_to_influxdb.py /src/forward_to_influxdb.py

# Install necessary Python packages if needed (uncomment if there are specific packages)
# RUN pip install -r /src/requirements.txt

# Stage 2: Extend sysdig image and copy Python installation from the previous stage
FROM sysdig/sysdig

# Install necessary dependencies
RUN yum install -y python3 python3-pip

# Copy the start script from the local machine to the build context
COPY start_sysdig.sh /src/start_sysdig.sh
RUN chmod +x /src/start_sysdig.sh

# Copy the Python script from the previous stage
COPY --from=python-base /src/forward_to_influxdb.py /src/forward_to_influxdb.py

# Set the entrypoint to run the start script
ENTRYPOINT ["/bin/bash", "-c", "/src/start_sysdig.sh"]
