#Script to collect container metrics from the influxdb
import requests
#from prometheus_api_client import PrometheusConnect, MetricSnapshotDataFrame, MetricRangeDataFrame
import pandas as pd
from datetime import datetime, timedelta
#from influxdb_client import InfluxDBClient, Point, WriteOptions
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np

influxdb_url = "http://localhost:5007"
token = "InfluxDBToken"
org = "MyOrg"
bucket = "Final"
bucket_logs = "Second_Logs"

##FETCH ALL METRICS FOR A TIME RANGE TO A DATA_FRAME
def fetch_all_metrics(time):
    client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
    
    query_api = client.query_api()
    data_frame = query_api.query_data_frame('from(bucket:"Final") '
                                            '|> range(start: -10m) '
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_measurement", "name", "value", "_time"])')
    #print(data_frame)
    print(data_frame[1])
    print(type(data_frame), len(data_frame))
    print(type(data_frame[1]))
    client.close()

#FETCH A SPECIFIC METRIC
def fetch_specific_metric(metric_name):
    client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)

    query_api = client.query_api()
    data_frame = query_api.query_data_frame('from(bucket: "Final") '
                                            '|> range(start: -10m) '
                                            '|> filter(fn: (r) => r._measurement == "container_cpu_system_seconds_total") '
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_measurement", "name", "value", "_time"])')
    print(data_frame)
    print(type(data_frame), len(data_frame))
    #print(type(data_frame[0]))
    client.close()

def fetch_logs():
    client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
    
    query_api = client.query_api()
    query = f'from(bucket: "{bucket_logs}") |> range(start: -5m) |> filter(fn: (r) => r["_measurement"] == "filelogs_ui") |> filter(fn: (r) => r["_field"] == "log")'
    result = query_api.query(query, org=org)
    print(result)
    
    for table in result:
        for record in table.records:
            timestamp = record.get_time()
            log_content = record.get_field()
            value = record.get_value()
            print("----LOG----")
            print(record, type(record))
            print(f"Timestamp: {timestamp}, Log Content: {log_content}")
            print(type(log_content))
            print("VALUE:", value)
            print("-----------")

    client.close()

def main():
    #fetch_all_metrics("5")
    fetch_all_metrics("10")
    print("AGORA SPECIFIV")
    fetch_specific_metric("container_cpu_system_seconds_total")
    print("AGOPRA LOGS")
    fetch_logs()

if __name__ == "__main__":
    main()
