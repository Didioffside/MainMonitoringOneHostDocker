# backup_script.sh
#!/bin/bash

# Enter the InfluxDB container and perform a backup
docker exec influxdb influx backup /backups --token InfluxDBToken
