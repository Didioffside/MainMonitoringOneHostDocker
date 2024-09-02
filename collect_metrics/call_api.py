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
from statistics import mean


def all_container_metrics(base_url):
    login_endpoint = f"{base_url}/login"
    cpu_endpoint = f"{base_url}/collect_metrics/all_container_metrics"

    login_data = {
        'username': 'test_user_api',
        'password': 'test_password_api'
    }

    #response = requests.post(login_endpoint, json=login_data)

    #if response.status_code == 200:
     #   print("FIZ LOGIN", flush=True)
      #  token = response.json().get('access_token')
       # print(f"Token received: {token}", flush=True)
        #            # Now make another request using the received token if needed
    #headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(cpu_endpoint, params={'start': '-5m'})

    if response.status_code == 200:

        print("DEU CERTO", flush=True)
        cpu_data = response.json()
        df_cpu = pd.DataFrame(cpu_data)
        print("CPU Metrics:", flush=True)
        print(df_cpu, flush=True)

    else:

        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)

    print("Also saving on folder: main_tests")
    directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/'
    if os.path.exists(directory):
        print(f"Directory '{directory}' already exists.")
    else:
        os.makedirs(directory, exist_ok=True)
        if os.path.exists(directory):
            print(f"Directory '{directory}' created successfully.")
    df_cpu.to_csv(directory+"/"+"main_test.csv", index=False)
        #print("SOU O TOKEN", token, flush=True)
    #else:
     #   print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)


    '''response = requests.get(cpu_endpoint, params={'start': '-30m'})  # Fetch data from the last 2 hours

    if response.status_code == 200:
    
        print("DEU CERTO", flush=True)
        cpu_data = response.json()
        df_cpu = pd.DataFrame(cpu_data)
        print("CPU Metrics:", flush=True)
        print(df_cpu, flush=True)
    
    else:
    
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)
    
    
    print("Also saving on folder: main_tests")
    directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/'
    if os.path.exists(directory):
        print(f"Directory '{directory}' already exists.")
    else:
        os.makedirs(directory, exist_ok=True)
        if os.path.exists(directory):
            print(f"Directory '{directory}' created successfully.")
    df_cpu.to_csv(directory+"/"+"main_test.csv", index=False)'''

def all_container_metrics_start_stop(base_url, start, stop, aux):
    cpu_endpoint = f"{base_url}/collect_metrics/all_container_metrics_start_stop"
    response = requests.get(cpu_endpoint, params={'start': start, 'stop': stop})  # Fetch data from the last 2 hours

    if response.status_code == 200:
    
        print("DEU CERTO", flush=True)
        cpu_data = response.json()
        df_cpu = pd.DataFrame(cpu_data)
        print("CPU Metrics:", flush=True)
        print(df_cpu, flush=True)
    
    else:
    
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)
    
    
    print("Also saving on folder: main_tests")
    directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/'
    if os.path.exists(directory):
        print(f"Directory '{directory}' already exists.")
    else:
        os.makedirs(directory, exist_ok=True)
        if os.path.exists(directory):
            print(f"Directory '{directory}' created successfully.")
    df_cpu.to_csv(directory+"/"+f"main_test{aux}.csv", index=False)

def all_container_cpu_metrics(base_url):
    
    cpu_endpoint = f"{base_url}/collect_metrics/all_container_cpu_metrics"
    response = requests.get(cpu_endpoint, params={'start': '-5m'})

    if response.status_code == 200:
        print("Request successful", flush=True)
        json_data_frames = response.json()

        # Convert JSON data frames to pandas DataFrames
        data_frames = []
        for df_json in json_data_frames:
            if isinstance(df_json, str):  # Check if it's a JSON string
                df_data = json.loads(df_json)  # Parse JSON string to Python object
                df = pd.DataFrame(df_data)  # Create DataFrame from Python object
                data_frames.append(df)
            elif isinstance(df_json, dict):  # Check if it's a JSON object
                df = pd.DataFrame(df_json)  # Create DataFrame directly
                data_frames.append(df)
            else:
                print("Invalid JSON data:", df_json)

        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/all_container_cpu_metrics'
        os.makedirs(directory, exist_ok=True)  # Ensure directory exists

        for i, df in enumerate(data_frames):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i}.csv'  # Use i+1 to start numbering from 1
            file_path = os.path.join(directory, file_name)
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'", flush=True)
    else:
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)

def all_container_memory_metrics(base_url):
    cpu_endpoint = f"{base_url}/collect_metrics/all_container_memory_metrics"
    response = requests.get(cpu_endpoint, params={'start': '-5m'})

    if response.status_code == 200:
        print("Request successful", flush=True)
        json_data_frames = response.json()

        # Convert JSON data frames to pandas DataFrames
        data_frames = []
        for df_json in json_data_frames:
            if isinstance(df_json, str):  # Check if it's a JSON string
                df_data = json.loads(df_json)  # Parse JSON string to Python object
                df = pd.DataFrame(df_data)  # Create DataFrame from Python object
                data_frames.append(df)
            elif isinstance(df_json, dict):  # Check if it's a JSON object
                df = pd.DataFrame(df_json)  # Create DataFrame directly
                data_frames.append(df)
            else:
                print("Invalid JSON data:", df_json)

        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/all_container_memory_metrics'
        os.makedirs(directory, exist_ok=True)  # Ensure directory exists

        for i, df in enumerate(data_frames):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i}.csv'  # Use i+1 to start numbering from 1
            file_path = os.path.join(directory, file_name)
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'", flush=True)
    else:
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)

def all_container_fs_metrics(base_url):

    cpu_endpoint = f"{base_url}/collect_metrics/all_container_fs_metrics"
    response = requests.get(cpu_endpoint, params={'start': '-5m'})

    if response.status_code == 200:
        print("Request successful", flush=True)
        json_data_frames = response.json()

        # Convert JSON data frames to pandas DataFrames
        data_frames = []
        for df_json in json_data_frames:
            if isinstance(df_json, str):  # Check if it's a JSON string
                df_data = json.loads(df_json)  # Parse JSON string to Python object
                df = pd.DataFrame(df_data)  # Create DataFrame from Python object
                data_frames.append(df)
            elif isinstance(df_json, dict):  # Check if it's a JSON object
                df = pd.DataFrame(df_json)  # Create DataFrame directly
                data_frames.append(df)
            else:
                print("Invalid JSON data:", df_json)

        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/all_container_fs_metrics'
        os.makedirs(directory, exist_ok=True)  # Ensure directory exists

        for i, df in enumerate(data_frames):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i}.csv'  # Use i+1 to start numbering from 1
            file_path = os.path.join(directory, file_name)
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'", flush=True)
    else:
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)

def all_container_network_metrics(base_url):
    cpu_endpoint = f"{base_url}/collect_metrics/all_container_network_metrics"
    response = requests.get(cpu_endpoint, params={'start': '-15m'})
    if response.status_code == 200:
    
        print("DEU CERTO", flush=True)
        cpu_data = response.json()
        df_cpu = pd.DataFrame(cpu_data)
        print("CPU Metrics:", flush=True)
        print(df_cpu, flush=True)
    
    else:
    
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)
    
    
    print("Also saving on folder: main_tests")
    directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/all_container_network_metrics'
    if os.path.exists(directory):
        print(f"Directory '{directory}' already exists.")
    else:
        os.makedirs(directory, exist_ok=True)
        if os.path.exists(directory):
            print(f"Directory '{directory}' created successfully.")
    df_cpu.to_csv(directory+"/"+"main_test.csv", index=False)
    '''if response.status_code == 200:
        print("Request successful", flush=True)
        json_data_frames = response.json()

        # Convert JSON data frames to pandas DataFrames
        data_frames = []
        for df_json in json_data_frames:
            if isinstance(df_json, str):  # Check if it's a JSON string
                df_data = json.loads(df_json)  # Parse JSON string to Python object
                df = pd.DataFrame(df_data)  # Create DataFrame from Python object
                data_frames.append(df)
            elif isinstance(df_json, dict):  # Check if it's a JSON object
                df = pd.DataFrame(df_json)  # Create DataFrame directly
                data_frames.append(df)
            else:
                print("Invalid JSON data:", df_json)

        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/all_container_network_metrics'
        os.makedirs(directory, exist_ok=True)  # Ensure directory exists

        for i, df in enumerate(data_frames):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i}.csv'  # Use i+1 to start numbering from 1
            file_path = os.path.join(directory, file_name)
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'", flush=True)
    else:
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)'''


def all_container_spec_metrics(base_url):
    cpu_endpoint = f"{base_url}/collect_metrics/all_container_spec_metrics"
    response = requests.get(cpu_endpoint, params={'start': '-5m'})

    if response.status_code == 200:
        print("Request successful", flush=True)
        json_data_frames = response.json()

        # Convert JSON data frames to pandas DataFrames
        data_frames = []
        for df_json in json_data_frames:
            if isinstance(df_json, str):  # Check if it's a JSON string
                df_data = json.loads(df_json)  # Parse JSON string to Python object
                df = pd.DataFrame(df_data)  # Create DataFrame from Python object
                data_frames.append(df)
            elif isinstance(df_json, dict):  # Check if it's a JSON object
                df = pd.DataFrame(df_json)  # Create DataFrame directly
                data_frames.append(df)
            else:
                print("Invalid JSON data:", df_json)

        directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/all_container_spec_metrics'
        os.makedirs(directory, exist_ok=True)  # Ensure directory exists

        for i, df in enumerate(data_frames):
            # Generate the file name (e.g., df_1.csv, df_2.csv, ...)
            file_name = f'df_{i}.csv'  # Use i+1 to start numbering from 1
            file_path = os.path.join(directory, file_name)
            
            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)  # Set index=False to exclude row numbers in CSV
            
            print(f"DataFrame {i+1} saved to '{file_path}'", flush=True)
    else:
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)


def all_node_metrics(base_url):

    cpu_endpoint = f"{base_url}/collect_metrics/all_node_metrics"
    response = requests.get(cpu_endpoint, params={'start': '-5m'})  # Fetch data from the last 2 hours

    if response.status_code == 200:
    
        print("DEU CERTO", flush=True)
        cpu_data = response.json()
        df_cpu = pd.DataFrame(cpu_data)
        print("CPU Metrics:", flush=True)
        print(df_cpu, flush=True)
    
    else:
    
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)
    
    
    print("Also saving on folder: main_tests_api")
    directory = '/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/'
    if os.path.exists(directory):
        print(f"Directory '{directory}' already exists.")
    else:
        os.makedirs(directory, exist_ok=True)
        if os.path.exists(directory):
            print(f"Directory '{directory}' created successfully.")
    df_cpu.to_csv(directory+"/"+"main_test_node.csv", index=False)


def main():


    base_url = "http://10.0.2.7:5010"
    all_container_metrics(base_url=base_url)
    '''df = pd.read_csv('/home/didioffside/MonitoringOneHost-main/collect_metrics/main_tests_api/main_test1.csv')
    column_names = df.columns.tolist()
    print(column_names, len(column_names))'''
    #all_container_metrics_start_stop(base_url, 1719235500, 1719236100, 0)

    #all_container_metrics_start_stop(base_url, 1719235500, 1719237299, 1)
    #all_container_metrics_start_stop(base_url, 1719237300, 1719239099, 2)
    #all_container_metrics_start_stop(base_url, 1719239100, 1719240899, 3)
    #all_container_metrics_start_stop(base_url, 1719240900, 1719242699, 4)
    #all_container_metrics_start_stop(base_url, 1719242700, 1719244499, 5)
    #all_container_metrics_start_stop(base_url, 1719244500, 1719246299, 6)
    #all_container_metrics_start_stop(base_url, 1719246300, 1719247200, 7)
    
    #all_container_cpu_metrics(base_url)
    #all_container_memory_metrics(base_url)
    #all_container_fs_metrics(base_url)
    #all_container_network_metrics(base_url)
    #all_container_spec_metrics(base_url)
    #all_node_metrics(base_url)
# Define the endpoint for CPU metrics
    
    
    
    '''influxdb_url = "http://172.17.0.1:5007"
    token = "InfluxDBToken"
    org = "MyOrg"
    bucket = "cadvisor_bucket"
    bucket_logs = "Second_Logs"
    bucket_networks = "Network"
    bucket_node = "node-exporter_bucket"
    time = 5'''

    #Select all container metrics
    #select_all_container_metrics(time, bucket, influxdb_url, token, org)

    #Select all host metrics
    #select_all_host_metrics(time, bucket_node, influxdb_url, token, org)

    #Function to return all packets
    #get_all_packets(time, bucket_networks, influxdb_url, token, org)

    #Function to get packet delays from ips
    #get_packet_delays(time, bucket_networks, influxdb_url, token, org, ip=True)

    #Function to get packet delays from protocols
    #get_packet_delays(time, bucket_networks, influxdb_url, token, org, protocol=True)
    
    #Function to get packet delays from ip and protocols
    #get_packet_delays(time, bucket_networks, influxdb_url, token, org, ip=True, protocol=True)



if __name__ == "__main__":

    main()