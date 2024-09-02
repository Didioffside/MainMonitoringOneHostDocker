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
import json

influxdb_url = "http://172.17.0.1:5007"
token = "InfluxDBToken"
org = "MyOrg"
bucket = "cadvisor_bucket"
bucket_logs = "Second_Logs"
bucket_networks = "Network"
bucket_node = "Final_Node"

def define_time():
    while True:
        time = input("Type the time from you which to select the metrics? (e.g., 10 for the last 10 min)")
        time = int(time)
        if isinstance(time, int) and int(time) > 0:
            return time
        else:
            print("Incorrect type, please type an integer number")

def select_all_container_metrics():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                                f'|> range(start: -{time}m) '
                                                '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
                                                #'|> keep(columns: ["_measurement", "name", "value", "_time"])')
        #print(data_frame)
        print("Also saving on folder: all_container_metrics")
        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/all_container_metrics/'
        if os.path.exists(directory):
            print(f"Directory '{directory}' already exists.")
        else:
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(directory):
                print(f"Directory '{directory}' created successfully.")
        for i, df in enumerate(data_frame):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i+1}.csv'  # Use i+1 to start numbering from 1
            file_path = directory + "/" + file_name
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'")

        client.close()

def select_specific_container_metrics():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        aux = 0
        while aux == 0:
            metric_name = input("Type the name of the specific metrric to retrieve (0 to leave)")
            if metric_name == "0":
                return -1
            data_frame = query_api.query_data_frame(f'from(bucket: "{bucket}") '
                                                    f'|> range(start: -{time}m) '
                                                    f'|> filter(fn: (r) => r._measurement == "{metric_name}") '
                                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
                                                    #'|> keep(columns: ["_measurement", "name", "value", "_time"])')
            
            if len(data_frame) > 0:
                print("Also saving on folder:specific_container_metrics")
                directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/specific_container_metrics/'
                if os.path.exists(directory):
                    print(f"Directory '{directory}' already exists.")
                else:
                    os.makedirs(directory, exist_ok=True)
                    if os.path.exists(directory):
                        print(f"Directory '{directory}' created successfully.")
                for i, df in enumerate(data_frame):
                    # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
                    file_name = f'df_{i+1}.csv'  # Use i+1 to start numbering from 1
                    file_path = directory + "/" + file_name
                    
                    # Save the DataFrame to CSV
                    df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
                    
                    print(f"DataFrame {i+1} saved to '{file_path}'")
                aux+=1
            else:
                print("That metric does not exist on the database or has no data in the specified time")
            #print(data_frame)
            #print(type(data_frame), len(data_frame))
            #print(type(data_frame[0]))
        client.close()
        return 0

def select_all_node_metrics():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                                f'|> range(start: -{time}m) '
                                                '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
                                                #'|> keep(columns: ["_measurement", "name", "value", "_time"])')
        print(data_frame)
        print("Also saving on folder: all_container_metrics")
        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/all_node_metrics/'
        if os.path.exists(directory):
            print(f"Directory '{directory}' already exists.")
        else:
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(directory):
                print(f"Directory '{directory}' created successfully.")
        for i, df in enumerate(data_frame):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i+1}.csv'  # Use i+1 to start numbering from 1
            file_path = directory + "/" + file_name
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'")

        client.close()

def select_specific_node_metrics():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        aux = 0
        while aux == 0:
            metric_name = input("Type the name of the specific metrric to retrieve (0 to leave)")
            if metric_name == "0":
                return -1
            data_frame = query_api.query_data_frame(f'from(bucket: "{bucket_node}") '
                                                    f'|> range(start: -{time}m) '
                                                    f'|> filter(fn: (r) => r._measurement == "{metric_name}") '
                                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
                                                    #'|> keep(columns: ["_measurement", "name", "value", "_time"])')
            
            if len(data_frame) > 0:
                print("Also saving on folder: specific_node_metrics")
                directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/specific_node_metrics/'
                if os.path.exists(directory):
                    print(f"Directory '{directory}' already exists.")
                else:
                    os.makedirs(directory, exist_ok=True)
                    if os.path.exists(directory):
                        print(f"Directory '{directory}' created successfully.")
                for i, df in enumerate(data_frame):
                    # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
                    file_name = f'df_{i+1}.csv'  # Use i+1 to start numbering from 1
                    file_path = directory + "/" + file_name
                    
                    # Save the DataFrame to CSV
                    df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
                    
                    print(f"DataFrame {i+1} saved to '{file_path}'")
                aux+=1
            else:
                print("That metric does not exist on the database or has no data in the specified time")
            #print(data_frame)
            #print(type(data_frame), len(data_frame))
            #print(type(data_frame[0]))
        client.close()
        return 0

def select_all_network_metrics():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                                f'|> range(start: -{time}m) '
                                                '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
                                                #'|> keep(columns: ["_measurement", "name", "value", "_time"])')
        print(data_frame)
        print("Also saving on folder: all_network_metrics")
        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/all_network_metrics/'
        if os.path.exists(directory):
            print(f"Directory '{directory}' already exists.")
        else:
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(directory):
                print(f"Directory '{directory}' created successfully.")
        for i, df in enumerate(data_frame):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i+1}.csv'  # Use i+1 to start numbering from 1
            file_path = directory + "/" + file_name
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'")

        client.close()

def select_specific_network_metrics():
    print("BRO")
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        aux = 0
        while aux == 0:
            metric_name = input("Type the name of the specific metrric to retrieve (0 to leave)")
            if metric_name == "0":
                return -1
            data_frame = query_api.query_data_frame(f'from(bucket: "{bucket_networks}") '
                                                    f'|> range(start: -{time}m) '
                                                    f'|> filter(fn: (r) => r._measurement == "{metric_name}") '
                                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
                                                    #'|> keep(columns: ["_measurement", "name", "value", "_time"])')
            
            if len(data_frame) > 0:
                print("Also saving on folder: specific_network_metrics")
                directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/specific_network_metrics/'
                if os.path.exists(directory):
                    print(f"Directory '{directory}' already exists.")
                else:
                    os.makedirs(directory, exist_ok=True)
                    if os.path.exists(directory):
                        print(f"Directory '{directory}' created successfully.")
                #for i, df in enumerate(data_frame):
                    # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
                 #   file_name = f'df_{i+1}.csv'  # Use i+1 to start numbering from 1
                    #file_path = directory + "/" + file_name
                    
                    # Save the DataFrame to CSV
                print("AQUI")
                data_frame.to_csv(directory+"/"+metric_name+".csv", index=False)  # Set index=False to exclude row numbers in CSV
                    
                    #print(f"DataFrame {i+1} saved to '{file_path}'")
                print("DATAFRAME SAVEd")
                aux+=1
            else:
                print("That metric does not exist on the database or has no data in the specified time")
            #print(data_frame)
            #print(type(data_frame), len(data_frame))
            #print(type(data_frame[0]))
        client.close()
        return 0
    
def select_all_logs():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        query_api = client.query_api()
        query = f'from(bucket: "{bucket_logs}") |> range(start: -{time}m) |> filter(fn: (r) => r["_field"] == "log")'
        result = query_api.query(query, org=org)
        if len(result) > 0:
            list_dict = []
            for table in result:
                for record in table.records:
                    timestamp = record.get_time()
                    log_content = record.get_field()
                    value = record.get_value()
                    measurement = record.get_measurement()
                    dict = {}
                    #dict["record"] = record
                    dict["timestamp"] = str(timestamp)
                    dict["log_content"] = str(log_content)
                    dict["value"] = str(value)
                    print("----LOG----")
                    print(record, type(record))
                    print(f"Timestamp: {timestamp}, Log Content: {log_content}")
                    print(type(log_content))
                    print("VALUE:", value)
                    print("-----------")
                    list_dict.append(dict)
                print("Also saving on folder: all_logs")
                directory = f'/home/didioffside/MonitoringOneHost-main/collect_metrics/all_logs/'
                if os.path.exists(directory):
                    print(f"Directory '{directory}' already exists.")
                else:
                    os.makedirs(directory, exist_ok=True)
                    if os.path.exists(directory):
                        print(f"Directory '{directory}' created successfully.")
            
            #file_path = "output.txt"
                directory = directory + "/" + str(measurement)+".txt"
                with open(directory, "w") as file:
                    json.dump(list_dict, file, indent=4)  # indent for pretty formatting
                    
                print(f"List of dictionaries saved to '{directory}'")
    
def select_specific_logs():
    time = define_time()
    if time:
        client = influxdb_client.InfluxDBClient(url=influxdb_url, token=token, org=org, timeout=30_000)
        
        query_api = client.query_api()
        aux = 0
        while aux == 0:
            name = input("Select the specific filelogs name of the service to collect logs (0 to leave)")
            if name == "0":
                return -1
            else:
                if isinstance(name, int) or name == "":
                    print("The type is incorrect")
                else:
                    query = f'from(bucket: "{bucket_logs}") |> range(start: -{time}m) |> filter(fn: (r) => r["_measurement"] == "{name}") |> filter(fn: (r) => r["_field"] == "log")'
                    result = query_api.query(query, org=org)
                    if len(result) > 0:
                        list_dict = []
                        for table in result:
                            for record in table.records:
                                timestamp = record.get_time()
                                log_content = record.get_field()
                                value = record.get_value()
                                dict = {}
                                #dict["record"] = record
                                dict["timestamp"] = str(timestamp)
                                dict["log_content"] = str(log_content)
                                dict["value"] = str(value)
                                print("----LOG----")
                                print(record, type(record))
                                print(f"Timestamp: {timestamp}, Log Content: {log_content}")
                                print(type(log_content))
                                print("VALUE:", value)
                                print("-----------")
                                list_dict.append(dict)
                        print("Also saving on folder: specific_logs")
                        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/specific_logs/'
                        if os.path.exists(directory):
                            print(f"Directory '{directory}' already exists.")
                        else:
                            os.makedirs(directory, exist_ok=True)
                            if os.path.exists(directory):
                                print(f"Directory '{directory}' created successfully.")
                        
                        #file_path = "output.txt"
                        directory = directory + "/" + str(name) + ".txt"
                        with open(directory, "w") as file:
                            json.dump(list_dict, file, indent=4)  # indent for pretty formatting
                            
                        print(f"List of dictionaries saved to '{directory}'")
                        
                        aux += 1
                    else:
                        print("The type was incorrect")    

        client.close()
    return 0

def show_menu():
    print("\n----- Main Menu -----")
    print("1. Select All Container Metrics")
    print("2. Select Specific Metric - Container")
    print("3. Show All Node Metrics")
    print("4. Select Specific Node Metric")
    print("5. Select All Network Metrics")
    print("6. Select Specific Network Metric")
    print("7. Select All Logs")
    print("8. Select Specific Logs")
    print("9. Exit")




def main():
    #fetch_all_metrics("10")
    print("A entrtar no menu")
    while True:
        show_menu()
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            select_all_container_metrics()
        elif choice == '2':
             select_specific_container_metrics()
        elif choice == '3':
             select_all_node_metrics()
        elif choice == '4':
             select_specific_node_metrics()
        elif choice == '5':
             select_all_network_metrics()
        elif choice == '6':
             select_specific_network_metrics()
        elif choice == '7':
             select_all_logs()
        elif choice == '8':
             select_specific_logs()
        elif choice == '9':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()