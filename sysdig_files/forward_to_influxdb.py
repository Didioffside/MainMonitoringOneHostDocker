import subprocess
import requests
import json

INFLUXDB_URL = "http://10.0.2.7:5007/"
SYSLOG_FILE = "/src/sysdig_output.scap"

def forward_to_influxdb(data):
    token = "InfluxDBToken"
    org = "MyOrg"
    # Prepare InfluxDB line protocol data
    payload = f"sysdig_events,host=your_host {data}"
    response = requests.post(INFLUXDB_URL, data=payload)
    if response.status_code != 204:
        print(f"Error sending data to InfluxDB: {response.text}")

def main():
    # Run sysdig capture
    cmd = ["sysdig", "-r", SYSLOG_FILE, "-pc"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    aux = 0
    for line in proc.stdout:
        if aux == 0:
            print("sou o 0!!!!!!!", flush=True)
        else:
            pass
        #forward_to_influxdb(line.decode("utf-8").strip())

if __name__ == "__main__":
    main()

