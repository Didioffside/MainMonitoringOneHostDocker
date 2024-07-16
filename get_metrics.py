import requests
from prometheus_api_client import PrometheusConnect, MetricSnapshotDataFrame, MetricRangeDataFrame
import pandas as pd
from datetime import datetime, timedelta
#from influxdb_client import InfluxDBClient, Point, WriteOptions
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np

def get_all_metrics(prometheus_url):
    metric_names_url = f"{prometheus_url}/api/v1/label/__name__/values"

    response = requests.get(metric_names_url)

    if response.status_code == 200:
        metric_names_data = response.json()
        return metric_names_data['data']
    else:
        print(f"Error: Unable to fetch metric names. Status code: {response.status_code}")
        return None

#def get_metric_info(prometheus_url, metric_name):
 #   metric_info_url = f"{prometheus_url}/api/v1/metadata"
  #  params = {'metric': metric_name}

   # response = requests.get(metric_info_url, params=params)

   # if response.status_code == 200:
    #    metric_info_data = response.json()
     #   return metric_info_data['data']
    #else:
     #   print(f"Error: Unable to fetch information for metric '{metric_name}'. Status code: {response.status_code}")
      #  return None
 
prometheus_url = 'http://localhost:9090'

metric_names = get_all_metrics(prometheus_url)
cont=0
if metric_names:
    print("List of Prometheus Metrics:")
    with open('thisfile.txt', 'w') as file:
        for metric_name in metric_names:
            file.write(str(metric_name))
            file.write("\n")
            print(f" - {metric_name}")
            cont+=1
    print(cont)

        #metric_info = get_metric_info(prometheus_url, metric_name)
        #if metric_info:
         #   print(f" Description: {metric_info['metric']['help']}")
          #  print(f" Type: {metric_info['type']}")
           # print("\n")

prometheus = PrometheusConnect(url=prometheus_url)

all_metrics = prometheus.all_metrics()

print(all_metrics)

metric_data = prometheus.get_current_metric_value(metric_name="container_cpu_usage_seconds_total")

print(metric_data)
metric_name="container_cpu_usage_seconds_total"
metric = metric_name+"{job='cadvisor', instance='cadvisor:8080'}"
metric_data = prometheus.get_current_metric_value(metric_name=metric,)
metric_df = MetricSnapshotDataFrame(metric_data)
#metric_data = prometheus.get_metric_range_data(metric_name=metric, start_time=(dt.datetime.now() - dt.timedelta(minutes=30)), end_time=dt.datetime.now(),)
#print(metric_data)
#metric_df = MetricRangeDataFrame(metric_data)

print(metric_df)
columns_to_drop = ['image', 'job', 'instance', 'container_label_author','container_label_com_docker_compose_config_hash','container_label_com_docker_compose_container_number','container_label_com_docker_compose_oneoff','container_label_com_docker_compose_project','container_label_com_docker_compose_project_config_files','container_label_com_docker_compose_project_working_dir','container_label_com_docker_compose_version','container_label_description','container_label_org_opencontainers_image_authors','container_label_org_opencontainers_image_created','container_label_org_opencontainers_image_description','container_label_org_opencontainers_image_documentation','container_label_org_opencontainers_image_licenses','container_label_org_opencontainers_image_revision','container_label_org_opencontainers_image_source','container_label_org_opencontainers_image_title','container_label_org_opencontainers_image_url','container_label_org_opencontainers_image_vendor','container_label_org_opencontainers_image_version','container_label_vendor','container_label_version','container_label_org_opencontainers_image_ref_name','container_label_maintainer']
metric_df=metric_df.drop(columns=columns_to_drop)
metric_df = metric_df.dropna(axis=0)
metric_df.to_csv('first_try.csv')
token = "XvBuopQ3GBDHQKlSeSOxx4V06LeWU-DYokS4snV-6Qga_lDdtPTr79nW7AwXNoJFjb8PasN2TJpRzeq1tI4pJA=="
org = "MyOrganization"
url = "http://localhost:8086"
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket2="MonitorBucket"
bucket="MyBucket"
bucket3="MetricBucket"
bucket4="Final"
bucket5="Logs"

##---------------------------------------------
##QUERY EXAMPLE 1 - FETCH ALL##
##query_api = client.query_api()
##data_frame = query_api.query_data_frame('from(bucket:"Final") '
  ##                                      '|> range(start: -10m) '
    ##                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
      ##                                  '|> keep(columns: ["_measurement", "service", "value", "_time"])')
##print(data_frame.to_string())
##print(type(data_frame))
##client.close()
##---------------------------------------------

##---------------------------------------------
##QUERY EXAMPLE 2 - FETCH SPECIFIC METRIC##
#query_api = client.query_api()
#data_frame = query_api.query_data_frame('from(bucket: "Final") '
 #                                       '|> range(start: -10m) '
  #                                      '|> filter(fn: (r) => r._measurement == "container_cpu_system_seconds_total") '
   #                                     '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
    #                                    '|> keep(columns: ["_measurement", "service", "value", "_time"])')
#print(data_frame.to_string())
#print(type(data_frame))
#client.close()
##---------------------------------------------------------------------------------------------

##---------------------------------------------------------------------------------------------
##QUERY EXAMPLE 3 - FETCH STORED LOGS##
query_api = client.query_api()
query = f'from(bucket: "{bucket5}") |> range(start: -5m) |> filter(fn: (r) => r["_measurement"] == "docker.ui") |> filter(fn: (r) => r["_field"] == "log")'
result = query_api.query(query, org=org)

for table in result:
    for record in table.records:
        timestamp = record.get_time()
        log_content = record.get_field()
        value = record.get_value()
        print(record, type(record))
        print(f"Timestamp: {timestamp}, Log Content: {log_content}")
        print(type(log_content))
        print("VALUEEEEE--------------", value)
client.close()
#logs = query_api.query('''
 #                      from(bucket:"Logs") |> range(start: -10m)
  #                     |> filter(fn: (r) => r["_measurement"] == "docker.service1")
   #                    |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn: "_seq")
    #                   |> keep(columns: ["_measurement", "docker.service1", "log"])''')
#print(logs)
#print(type(logs))
#for table_index, table in enumerate(logs):
#    print(f"Table {table_index+1}:")
#    for row_index, row in enumerate(table.records):
#        print(f"Row {row_index+1}:")
#        for column_name, column_value in row.values.items():
#            print(f"{column_name}: {column_value}")
#    print("-" * 30)

##----------------------------------------------

#------EXEMPLO--------
#_now = datetime.utcnow()
#_data_frame = pd.DataFrame(data=[["metrica1", 5.0], ["metrica2", 7.0]],
 #                         index=[_now, _now + timedelta(hours=1)],
  #                        columns=["locationz", "water_high"])
#write_api = client.write_api(write_options=SYNCHRONOUS)
#write_api.write(bucket3, org, record=_data_frame, data_frame_measurement_name='h2o_feet1', data_frame_tag_columns=['location'])

##write_api = client.write_api(write_options=SYNCHRONOUS)
#write_api = client.write_api(write_options=SYNCHRONOUS)
##columns_names = metric_df.columns
##columns_list = metric_df.columns.tolist()

'''
metric_names = [item for item in metric_names if item.startswith('container')]
metric_names.remove("container_scrape_error")
for metric in metric_names:
        print(metric, flush=True)
        #add labels to metric name
        metric_name = metric+"{job='cadvisor', instance='cadvisor:8080'}"
        #fetch all data from that metric and labels
        metric_data = prometheus.get_current_metric_value(metric_name=metric_name)
        #turn data into a dataframe (pandas)
        metric_df = MetricSnapshotDataFrame(metric_data)
        #drop useless columns
        columns_to_drop = ['image', 'job', 'instance', 'container_label_author','container_label_com_docker_compose_config_hash','container_label_com_docker_compose_container_number','container_label_com_docker_compose_oneoff','container_label_com_docker_compose_project','container_label_com_docker_compose_project_config_files','container_label_com_docker_compose_project_working_dir','container_label_com_docker_compose_version','container_label_description','container_label_org_opencontainers_image_authors','container_label_org_opencontainers_image_created','container_label_org_opencontainers_image_description','container_label_org_opencontainers_image_documentation','container_label_org_opencontainers_image_licenses','container_label_org_opencontainers_image_revision','container_label_org_opencontainers_image_source','container_label_org_opencontainers_image_title','container_label_org_opencontainers_image_url','container_label_org_opencontainers_image_vendor','container_label_org_opencontainers_image_version','container_label_vendor','container_label_version','container_label_org_opencontainers_image_ref_name','container_label_maintainer']
        columns_to_keep = ['__name__', 'container_label_com_docker_compose_service', 'id', 'name', 'value']
        metric_df = metric_df[columns_to_keep]
        #drop lines with nan also
        metric_df = metric_df.dropna(axis=0)

        #INFLUXDB PART
        #define credentials
        token = os.environ.get("INFLUXDB_TOKEN")
        org = "MyOrganization"
        url = "http://localhost:8086"
        #connect client
        client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
        #declare intended bucket
        bucket = "Final"
        #define timestamp
        _now = datetime.utcnow()
        #define write db options
        write_api = client.write_api(write_options=SYNCHRONOUS)
        #save columns names of df
        columns_names = metric_df.columns
        columns_list = metric_df.columns.tolist()

        #iterate through df
        for index, row in metric_df.iterrows():
            #save current values
            name = row['__name__']
            service = row['container_label_com_docker_compose_service']
            value = row['value']
            #timestamp = row['timestamp']
            id = row['id']
            second_name = row['name']
            write_api.write(bucket, org, Point("Metricas").tag(service, second_name).field(name, value).time(_now))
       ''' 

'''for index, row in metric_df.iterrows():
    print(index, row['value'])
    print(type(row['container_label_com_docker_compose_service']), flush=True)

    name = row['__name__']
    service = row['container_label_com_docker_compose_service']
    value = row['value']
    timestamp = row['timestamp']
    id = row['id']
    second_name = row['name']
    columns_to_drop = ['timestamp', 'cpu']
    new_new_df=metric_df.drop(columns=columns_to_drop)
    new_columns = new_new_df.columns.tolist()
    print(new_columns)
    write_api.write(bucket4, org, Point("Metricas").tag(service, second_name).field(name, value).time(_now))
    #new_frame = pd.DataFrame(data=[[name, service, id, second_name, value], [name, service, id, second_name, value+2]], 
     #                        index = [timestamp, timestamp],
      #                       columns = new_columns)
    #print(new_frame)
    #write_api.write(bucket3, org, record_data=new_frame, data_frame_measurement_name=name, data_frame_tag_columns=[service, second_name])

'''
'''
print(columns_names, flush=True)
print(columns_list, flush=True)
print("acabei crl", flush=True)'''
#with InfluxDBClient(url="http://localhost:8086", token="XvBuopQ3GBDHQKlSeSOxx4V06LeWU-DYokS4snV-6Qga_lDdtPTr79nW7AwXNoJFjb8PasN2TJpRzeq1tI4pJA==", org="MyOrganization") as _client:
 #   with _client.write_api(write_options=WriteOptions(batch_size=500,
  #                                                    flush_interval=10_000,
   #                                                   jitter_interval=2_000,
    #                                                  retry_interval=5_000,
     #                                                 max_retries=5,
      #                                                max_retry_delay=30_000,
       #                                               max_close_wait=300_000,
        #                                              exponential_base=2)) as _write_client:
        #_write_client.write("MyBucket", "MyOrganization", record=metric_df, data_frame_measurement_name='metrics', data_frame_tag_columns=['value'])
#print("chewugiue ca")
#metric_df = MetricSnapshotDataFrame(metric_data)
#print(metric_df)
#print(metric_df.head())
#metric_df.to_excel("output.xlsx", index=False)

'''
token = os.environ.get("INFLUXDB_TOKEN")
org = "MyOrganization"
url = "http://localhost:8086"

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

bucket="MyBucket"
bucket2="MonitorBucket"

write_api = client.write_api(write_options=SYNCHRONOUS)
#metric_df.set_index("_time")
_now = datetime.utcnow()
metric_df.set_index=(_now, _now + timedelta(minutes=5))
write_api.write(bucket2, org, record=metric_df, data_frame_measurement_name='metricas_teste')'''
'''  
for value in range(5):
  point = (
    Point("measurement1")
    .tag("tagname1", "tagvalue1")
    .field("field1", value)
  )
  write_api.write(bucket=bucket, org="MyOrganization", record=point)
  time.sleep(1) # separate points by 1 second
'''
'''
query_api = client.query_api()
query = """from(bucket: "MyBucket")
 |> range(start: -10m)
 |> filter(fn: (r) => r._measurement == "measurement1")"""
tables = query_api.query(query, org="MyOrganization")

for table in tables:
  for record in table.records:
    print(record)'''


