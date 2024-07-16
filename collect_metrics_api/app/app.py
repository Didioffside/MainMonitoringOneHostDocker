from flask import Flask, request, jsonify, Response
from influxdb_client import InfluxDBClient, Point, Dialect
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
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_httpauth import HTTPTokenAuth
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'APItokenACCESS'  # Change this to a random secret key
jwt = JWTManager(app)

INFLUXDB_URL = "http://172.17.0.1:5007"
INFLUXDB_TOKEN = "InfluxDBToken"
INFLUXDB_ORG = "MyOrg"
bucket = "cadvisor_bucket"
bucket_logs = "Second_Logs"
bucket_networks = "Network"
bucket_node = "node-exporter_bucket"

time_range_default = 5

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

# User Authentication for login endpoint
users = {
    "test_user_api": "test_password_api"  # Example user credentials
}

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    print("aqui", username, flush=True)
    print("e aqui", password, flush=True)
    if username not in users or users[username] != password:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)


#CONTAINER METRICS - CADVISOR
@app.route('/collect_metrics/all_container_metrics', methods=['GET'])
@jwt_required()
def get_all_container_metrics():
    start = request.args.get('start', '-10m') 
    stop = request.args.get('stop', 'now') 
    #query = f'from(bucket: "{bucket}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "cpu")'
    #result = query_api.query(org=INFLUXDB_ORG, query=query)
    
    df = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                    f'|> range(start: {start}) '
                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
    if isinstance(df, list):
           df = pd.concat(df, ignore_index=True)

    return Response(df.to_json(orient="records"), mimetype='application/json')
    
    #return jsonify(metrics)

@app.route('/collect_metrics/all_container_metrics_start_stop', methods=['GET'])
@jwt_required()
def get_all_container_metrics_start_stop():
    curr_unix = get_curr_unix_time()
    unix_time_ago = get_x_time_ago_unix_time(10)
    start = request.args.get('start', unix_time_ago) 
    stop = request.args.get('stop', curr_unix) 
    #query = f'from(bucket: "{bucket}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "cpu")'
    #result = query_api.query(org=INFLUXDB_ORG, query=query)

    df = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                    f'|> range(start: {start}, stop: {stop}) '
                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
    if isinstance(df, list):
           df = pd.concat(df, ignore_index=True)

    return Response(df.to_json(orient="records"), mimetype='application/json')
    
    #return jsonify(metrics)


@app.route('/collect_metrics/all_container_cpu_metrics', methods=['GET'])
@jwt_required()
def get_all_container_cpu_metrics():
     
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^container_cpu_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_container_memory_metrics', methods=['GET'])
@jwt_required()
def get_all_container_memory_metrics():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            '|> filter(fn: (r) => r._measurement =~ /^container_memory_/)'
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> group(columns: ["_measurement"]) ')

    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_container_fs_metrics', methods=['GET'])
@jwt_required()
def get_all_container_fs_metrics():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            '|> filter(fn: (r) => r._measurement =~ /^container_fs_/)'
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> group(columns: ["_measurement"]) ')

    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_container_network_metrics', methods=['GET'])
@jwt_required()
def get_all_container_network_metrics():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            '|> filter(fn: (r) => r._measurement =~ /^container_network_/)'
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> group(columns: ["_measurement"]) ')
    unique_measuements = pd.unique(data_frames['_measurement'])
    print("AQUI", data_frames, type(data_frames), len(data_frames), unique_measuements, flush=True)
    '''new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]'''
    return Response(data_frames.to_json(orient="records"), mimetype='application/json')
    #return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_container_spec_metrics', methods=['GET'])
@jwt_required()
def get_all_container_spec_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            '|> filter(fn: (r) => r._measurement =~ /^container_spec_/)'
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> group(columns: ["_measurement"]) ')

    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')
################################################################################################################################################################
#NODE/HOST METRICS - NODE-EXPORTER
@app.route('/collect_metrics/all_node_metrics', methods=['GET'])
@jwt_required()
def get_all_node_metrics():

    start = request.args.get('start', '-10m') 
    stop = request.args.get('stop', 'now') 
    #query = f'from(bucket: "{bucket}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "cpu")'
    #result = query_api.query(org=INFLUXDB_ORG, query=query)
    
    df = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                    f'|> range(start: {start}) '
                                    '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
    if isinstance(df, list):
           df = pd.concat(df, ignore_index=True)

    return Response(df.to_json(orient="records"), mimetype='application/json')

@app.route('/collect_metrics/all_node_cooling', methods=['GET'])
@jwt_required()
def get_all_node_cooling_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_cooling_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')
    
@app.route('/collect_metrics/all_node_cpu', methods=['GET'])
@jwt_required()
def get_all_node_cpu_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_cpu_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_disk', methods=['GET'])
@jwt_required()
def get_all_node_disk_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_disk_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_filesystem', methods=['GET'])
@jwt_required()
def get_all_node_filesystem_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_filesystem_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_memory', methods=['GET'])
@jwt_required()
def get_all_node_memory_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_memory_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_netstat', methods=['GET'])
@jwt_required()
def get_all_node_netstat_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_netstat_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_network', methods=['GET'])
@jwt_required()
def get_all_node_network_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_network_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_power', methods=['GET'])
@jwt_required()
def get_all_node_power_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_power_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_pressure', methods=['GET'])
@jwt_required()
def get_all_node_pressure_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_pressure_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_schedstat', methods=['GET'])
@jwt_required()
def get_all_node_schedstat_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_schedstat_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_sockstat', methods=['GET'])
@jwt_required()
def get_all_node_sockstat_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_sockstat_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_softnet', methods=['GET'])
@jwt_required()
def get_all_node_softnet_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_softnet_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_time', methods=['GET'])
@jwt_required()
def get_all_node_time_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_time_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_timex', methods=['GET'])
@jwt_required()
def get_all_node_timex_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_timex_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')

@app.route('/collect_metrics/all_node_vmstat', methods=['GET'])
@jwt_required()
def get_all_node_vmstat_metrics():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 
    
    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_node}") '
                                             f'|> range(start: {start}) '
                                             '|> filter(fn: (r) => r._measurement =~ /^node_vmstat_/)'
                                             '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                             '|> group(columns: ["_measurement"]) ')

    print("chego ca", flush=True)
    new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')
#################################################################################################################################################################
#NETWORK METRICS - FROM PACKETS AND PYSHARK

@app.route('/collect_metrics/all_packets', methods=['GET'])
@jwt_required()
def get_all_packets():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                                f'|> range(start: {start}) '
                                                '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
    
    print("chego ca", flush=True)
    '''new_df_list = []
    for df in data_frames:
        unique_measurements = pd.unique(df['_measurement'])
        if len(unique_measurements) > 1:
            for u in unique_measurements:
                new_df_list.append(df[df['_measurement']==str(u)])
        else:
            new_df_list.append(df[df['_measurement']==str(unique_measurements[0])])
         
    json_data_frames = [df.to_json(orient="records") for df in new_df_list]
    
    return Response(json.dumps(json_data_frames), mimetype='application/json')'''
    if isinstance(data_frames, list):
        data_frames = pd.concat(data_frames, ignore_index=True)

    return Response(data_frames.to_json(orient="records"), mimetype='application/json')
    
@app.route('/collect_metrics/all_packets_start_stop', methods=['GET'])
@jwt_required()
def get_all_packets_start_stop():

    curr_unix = get_curr_unix_time()
    unix_time_ago = get_x_time_ago_unix_time(10)

    start = request.args.get('start', unix_time_ago)
    stop = request.args.get('stop', curr_unix) 

    data_frames = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                                f'|> range(start: {start}, stop: {stop}) '
                                                '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") ')
    
    print("chego ca", type(data_frames), len(data_frames), flush=True)
    if isinstance(data_frames, list):
        data_frames = pd.concat(data_frames, ignore_index=True)

    return Response(data_frames.to_json(orient="records"), mimetype='application/json')
    #return Response(json.dumps(json_data_frames), mimetype='application/json')

#no start_stop
@app.route('/collect_metrics/all_packets_delay_ip', methods=['GET'])
@jwt_required()
def get_all_packets_delay_ip():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    measurement_name = "packets"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_time", "dst_ip"])')
    
    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['dst_ip'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_delays = []
    avg_delays_per_ip = {}
    for df in list_df:
        df = df.sort_values('_time')
        rows = df['_time'].tolist()
        avg_delay = calculate_avg_delay(rows)
        list_avg_delays.append(avg_delay)

    for i in range(len(list_avg_delays)):
        avg_delays_per_ip[unique_ips[i]] = list_avg_delays[i].to_json()
    return jsonify(avg_delays_per_ip)

@app.route('/collect_metrics/all_packets_delay_protocol', methods=['GET'])
@jwt_required()
def get_all_packets_delay_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    measurement_name = "packets"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_time", "protocol"])')
    
    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['protocol'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_delays = []
    avg_delays_per_ip = {}
    for df in list_df:
        df = df.sort_values('_time')
        rows = df['_time'].tolist()
        avg_delay = calculate_avg_delay(rows)
        list_avg_delays.append(avg_delay)

    for i in range(len(list_avg_delays)):
        avg_delays_per_ip[unique_ips[i]] = list_avg_delays[i].to_json()
    return jsonify(avg_delays_per_ip)

@app.route('/collect_metrics/all_packets_delay_ip_protocol', methods=['GET'])
@jwt_required()
def get_all_packest_delay_ip_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    measurement_name = "packets"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_time", "dst_ip", "protocol"])')
    
    auxaux = 0
    all_list = []
    avg_delays_tcp = {}
    avg_delays_udp = {}
    avg_delays_icmp = {}
    avg_delays_sctp = {}
    avg_delays_igmp = {}
    for df in data_frame:
        auxaux+=1
        if 'dst_ip' in df.columns and 'protocol' in df.columns:
            #print("OLA")
            unique_val_table = pd.unique(df['table'])
            unique_ips = pd.unique(df['dst_ip'])
            unique_protocols = pd.unique(df['protocol'])
            list_df = []
            aux = 1
            while aux <= len(unique_val_table):
                list_df.append(df[df['table']==unique_val_table[aux-1]])
                aux += 1
            how_many = 0
            for df in list_df:
                how_many+=1
                df = df.sort_values('_time')
                ip = pd.unique(df['dst_ip'])
                tcp = df[df['protocol']=='TCP']
                rows = tcp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_tcp[ip[0]] = avg_delay.to_json()
                udp = df[df['protocol']=='UDP']
                rows = udp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_udp[ip[0]] = avg_delay.to_json()
                icmp = df[df['protocol']=='ICMP']
                rows = icmp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_icmp[ip[0]] = avg_delay.to_json()
                sctp = df[df['protocol']=='SCTP']
                rows = sctp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_sctp[ip[0]] = avg_delay.to_json()
                igmp = df[df['protocol']=='IGMP']
                rows = igmp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_igmp[ip[0]] = avg_delay.to_json()
    
    #print("AVG DELAYS TCP", avg_delays_tcp)
    #print("AVG DELAYS UDP", avg_delays_udp)
    #print("AVG DELAYS ICMP", avg_delays_icmp)
    #print("AVG DELAYS SCTP", avg_delays_sctp)
    #print("AVG DELAYS IGMP", avg_delays_igmp)
    all_list.append(avg_delays_tcp)
    all_list.append(avg_delays_udp)
    all_list.append(avg_delays_icmp)
    all_list.append(avg_delays_sctp)
    all_list.append(avg_delays_igmp)
    #print("HOW_MANY", how_many)
    #print(auxaux)
    return jsonify(all_list)

@app.route('/collect_metrics/all_packet_sizes', methods=['GET'])
@jwt_required()
def get_all_packet_sizes():
    
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length"])')
    df = data_frame['length'].tolist()
    mean_size = mean(df)
    return jsonify({"mean": mean_size})

@app.route('/collect_metrics/all_packet_sizes_ip', methods=['GET'])
@jwt_required()
def get_all_packet_sizes_ip():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length", "dst_ip"])')

    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['dst_ip'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_length = []
    avg_length_per_ip = {}
    for df in list_df:
        #df = df.sort_values('_time')
        rows = df['length'].tolist()
        #avg_delay = calculate_avg_delay(rows)
        avg_length = mean(rows)
        list_avg_length.append(avg_length)

    for i in range(len(list_avg_length)):
        avg_length_per_ip[unique_ips[i]] = list_avg_length[i].to_json()
    return jsonify(avg_length_per_ip)

@app.route('/collect_metrics/all_packet_sizes_protocol', methods=['GET'])
@jwt_required()
def get_all_packet_sizes_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length", "protocol"])')

    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['protocol'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_length = []
    avg_length_per_ip = {}
    for df in list_df:
        #df = df.sort_values('_time')
        rows = df['length'].tolist()
        #avg_delay = calculate_avg_delay(rows)
        avg_length = mean(rows)
        list_avg_length.append(avg_length)

    for i in range(len(list_avg_length)):
        avg_length_per_ip[unique_ips[i]] = list_avg_length[i].to_json()
    return jsonify(avg_length_per_ip)    

@app.route('/collect_metrics/all_packet_sizes_ip_protocol', methods=['GET'])
@jwt_required()
def get_all_packet_sizes_ip_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length", "ip", "protocol"])')

    all_list = []
    auxaux = 0
    avg_sizes_tcp = {}
    avg_sizes_udp = {}
    avg_sizes_icmp = {}
    avg_sizes_sctp = {}
    avg_sizes_igmp = {}
    for df in data_frame:
        auxaux+=1
        if 'dst_ip' in df.columns and 'protocol' in df.columns:
            print("OLA")
            unique_val_table = pd.unique(df['table'])
            unique_ips = pd.unique(df['dst_ip'])
            unique_protocols = pd.unique(df['protocol'])
            list_df = []
            aux = 1
            while aux <= len(unique_val_table):
                list_df.append(df[df['table']==unique_val_table[aux-1]])
                aux += 1
            #how_many = 0
            for df in list_df:
                #how_many+=1
                #df = df.sort_values('_time')
                ip = pd.unique(df['dst_ip'])
                tcp = df[df['protocol']=='TCP']
                rows = tcp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_tcp[ip[0]] = avg_size.to_json()
                udp = df[df['protocol']=='UDP']
                rows = udp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_udp[ip[0]] = avg_size.to_json()
                icmp = df[df['protocol']=='ICMP']
                rows = icmp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_icmp[ip[0]] = avg_size.to_json()
                sctp = df[df['protocol']=='SCTP']
                rows = sctp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_sctp[ip[0]] = avg_size.to_json()
                igmp = df[df['protocol']=='IGMP']
                rows = igmp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_igmp[ip[0]] = avg_size.to_json()
    all_list.append(avg_sizes_tcp)
    all_list.append(avg_sizes_udp)
    all_list.append(avg_sizes_icmp)
    all_list.append(avg_sizes_sctp)
    all_list.append(avg_sizes_igmp)
    return jsonify(all_list)

@app.route('/collect_metrics/all_byte_rate_received', methods=['GET'])
@jwt_required()
def get_all_byte_rate_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_bytes_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/all_byte_rate_transmitted', methods=['GET'])
@jwt_required()
def get_all_byte_rate_transmitted():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_bytes_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/all_packet_rate_received', methods=['GET'])
@jwt_required()
def get_all_packet_rate_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_packets_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/all_packet_rate_transmitted', methods=['GET'])
@jwt_required()
def get_all_packet_rate_transmitted():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_packets_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/number_packets_received', methods=['GET'])
@jwt_required()
def get_number_packets_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_packets_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)

@app.route('/collect_metrics/number_packets_transmit', methods=['GET'])
@jwt_required()
def get_number_packets_transmit():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_packets_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)

@app.route('/collect_metrics/number_bytes_received', methods=['GET'])
@jwt_required()
def get_number_bytes_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_bytes_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)

@app.route('/collect_metrics/number_bytes_transmit', methods=['GET'])
@jwt_required()
def get_number_bytes_transmit():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_bytes_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)
'''
#start_stop
@app.route('/collect_metrics/all_packets_delay_ip', methods=['GET'])
def get_all_packets_delay_ip():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    measurement_name = "packets"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_time", "dst_ip"])')
    
    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['dst_ip'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_delays = []
    avg_delays_per_ip = {}
    for df in list_df:
        df = df.sort_values('_time')
        rows = df['_time'].tolist()
        avg_delay = calculate_avg_delay(rows)
        list_avg_delays.append(avg_delay)

    for i in range(len(list_avg_delays)):
        avg_delays_per_ip[unique_ips[i]] = list_avg_delays[i].to_json()
    return jsonify(avg_delays_per_ip)

@app.route('/collect_metrics/all_packets_delay_protocol', methods=['GET'])
def get_all_packets_delay_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    measurement_name = "packets"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_time", "protocol"])')
    
    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['protocol'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_delays = []
    avg_delays_per_ip = {}
    for df in list_df:
        df = df.sort_values('_time')
        rows = df['_time'].tolist()
        avg_delay = calculate_avg_delay(rows)
        list_avg_delays.append(avg_delay)

    for i in range(len(list_avg_delays)):
        avg_delays_per_ip[unique_ips[i]] = list_avg_delays[i].to_json()
    return jsonify(avg_delays_per_ip)

@app.route('/collect_metrics/all_packets_delay_ip_protocol', methods=['GET'])
def get_all_packest_delay_ip_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now') 

    measurement_name = "packets"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["_time", "dst_ip", "protocol"])')
    
    auxaux = 0
    all_list = []
    avg_delays_tcp = {}
    avg_delays_udp = {}
    avg_delays_icmp = {}
    avg_delays_sctp = {}
    avg_delays_igmp = {}
    for df in data_frame:
        auxaux+=1
        if 'dst_ip' in df.columns and 'protocol' in df.columns:
            #print("OLA")
            unique_val_table = pd.unique(df['table'])
            unique_ips = pd.unique(df['dst_ip'])
            unique_protocols = pd.unique(df['protocol'])
            list_df = []
            aux = 1
            while aux <= len(unique_val_table):
                list_df.append(df[df['table']==unique_val_table[aux-1]])
                aux += 1
            how_many = 0
            for df in list_df:
                how_many+=1
                df = df.sort_values('_time')
                ip = pd.unique(df['dst_ip'])
                tcp = df[df['protocol']=='TCP']
                rows = tcp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_tcp[ip[0]] = avg_delay.to_json()
                udp = df[df['protocol']=='UDP']
                rows = udp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_udp[ip[0]] = avg_delay.to_json()
                icmp = df[df['protocol']=='ICMP']
                rows = icmp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_icmp[ip[0]] = avg_delay.to_json()
                sctp = df[df['protocol']=='SCTP']
                rows = sctp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_sctp[ip[0]] = avg_delay.to_json()
                igmp = df[df['protocol']=='IGMP']
                rows = igmp['_time'].tolist()
                avg_delay = calculate_avg_delay(rows)
                avg_delays_igmp[ip[0]] = avg_delay.to_json()
    
    #print("AVG DELAYS TCP", avg_delays_tcp)
    #print("AVG DELAYS UDP", avg_delays_udp)
    #print("AVG DELAYS ICMP", avg_delays_icmp)
    #print("AVG DELAYS SCTP", avg_delays_sctp)
    #print("AVG DELAYS IGMP", avg_delays_igmp)
    all_list.append(avg_delays_tcp)
    all_list.append(avg_delays_udp)
    all_list.append(avg_delays_icmp)
    all_list.append(avg_delays_sctp)
    all_list.append(avg_delays_igmp)
    #print("HOW_MANY", how_many)
    #print(auxaux)
    return jsonify(all_list)

@app.route('/collect_metrics/all_packet_sizes', methods=['GET'])
def get_all_packet_sizes():
    
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length"])')
    df = data_frame['length'].tolist()
    mean_size = mean(df)
    return jsonify({"mean": mean_size})

@app.route('/collect_metrics/all_packet_sizes_ip', methods=['GET'])
def get_all_packet_sizes_ip():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length", "dst_ip"])')

    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['dst_ip'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_length = []
    avg_length_per_ip = {}
    for df in list_df:
        #df = df.sort_values('_time')
        rows = df['length'].tolist()
        #avg_delay = calculate_avg_delay(rows)
        avg_length = mean(rows)
        list_avg_length.append(avg_length)

    for i in range(len(list_avg_length)):
        avg_length_per_ip[unique_ips[i]] = list_avg_length[i].to_json()
    return jsonify(avg_length_per_ip)

@app.route('/collect_metrics/all_packet_sizes_protocol', methods=['GET'])
def get_all_packet_sizes_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length", "protocol"])')

    unique_val_table = len(pd.unique(data_frame[1]['table']))
    unique_ips = pd.unique(data_frame[1]['protocol'])
    data_frame = data_frame[1]
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i+1])

    list_avg_length = []
    avg_length_per_ip = {}
    for df in list_df:
        #df = df.sort_values('_time')
        rows = df['length'].tolist()
        #avg_delay = calculate_avg_delay(rows)
        avg_length = mean(rows)
        list_avg_length.append(avg_length)

    for i in range(len(list_avg_length)):
        avg_length_per_ip[unique_ips[i]] = list_avg_length[i].to_json()
    return jsonify(avg_length_per_ip)    

@app.route('/collect_metrics/all_packet_sizes_ip_protocol', methods=['GET'])
def get_all_packet_sizes_ip_protocol():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "packets"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket_networks}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["length", "ip", "protocol"])')

    all_list = []
    auxaux = 0
    avg_sizes_tcp = {}
    avg_sizes_udp = {}
    avg_sizes_icmp = {}
    avg_sizes_sctp = {}
    avg_sizes_igmp = {}
    for df in data_frame:
        auxaux+=1
        if 'dst_ip' in df.columns and 'protocol' in df.columns:
            print("OLA")
            unique_val_table = pd.unique(df['table'])
            unique_ips = pd.unique(df['dst_ip'])
            unique_protocols = pd.unique(df['protocol'])
            list_df = []
            aux = 1
            while aux <= len(unique_val_table):
                list_df.append(df[df['table']==unique_val_table[aux-1]])
                aux += 1
            #how_many = 0
            for df in list_df:
                #how_many+=1
                #df = df.sort_values('_time')
                ip = pd.unique(df['dst_ip'])
                tcp = df[df['protocol']=='TCP']
                rows = tcp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_tcp[ip[0]] = avg_size.to_json()
                udp = df[df['protocol']=='UDP']
                rows = udp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_udp[ip[0]] = avg_size.to_json()
                icmp = df[df['protocol']=='ICMP']
                rows = icmp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_icmp[ip[0]] = avg_size.to_json()
                sctp = df[df['protocol']=='SCTP']
                rows = sctp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_sctp[ip[0]] = avg_size.to_json()
                igmp = df[df['protocol']=='IGMP']
                rows = igmp['length'].tolist()
                if len(rows) > 1:
                    avg_size = mean(rows)
                else:
                    if len(rows)==1:
                        avg_size = rows[0]
                    else:
                        avg_size = 0
                avg_sizes_igmp[ip[0]] = avg_size.to_json()
    all_list.append(avg_sizes_tcp)
    all_list.append(avg_sizes_udp)
    all_list.append(avg_sizes_icmp)
    all_list.append(avg_sizes_sctp)
    all_list.append(avg_sizes_igmp)
    return jsonify(all_list)

@app.route('/collect_metrics/all_byte_rate_received', methods=['GET'])
def get_all_byte_rate_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_bytes_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/all_byte_rate_transmitted', methods=['GET'])
def get_all_byte_rate_transmitted():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_bytes_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/all_packet_rate_received', methods=['GET'])
def get_all_packet_rate_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_packets_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/all_packet_rate_transmitted', methods=['GET'])
def get_all_packet_rate_transmitted():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_packets_total"

    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                        f'|> range(start: {start}) '
                                        f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                        '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                        '|> keep(columns: ["_time", "interface", "counter"])')
    
    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    print(unique_val_table, unique_in)
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    packet_rate_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        sum_values = sum(values)
        print("SOU A UNIQUE INTERFACE", unique_in, sum_values)

        aux = df.sort_values('_time')
        time_ = aux['_time'].tolist()
        print(len(time_))
        if len(time_) > 1:
            seconds = (time_[len(time_)-1] - time_[0]).total_seconds()
            print("SECONDS", seconds, unique_in)

            packet_rate_per_interface[unique_in[0]] = (sum_values/seconds).to_json()
    return jsonify(packet_rate_per_interface)

@app.route('/collect_metrics/number_packets_received', methods=['GET'])
def get_number_packets_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_packets_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)

@app.route('/collect_metrics/number_packets_transmit', methods=['GET'])
def get_number_packets_transmit():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_packets_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)

@app.route('/collect_metrics/number_bytes_received', methods=['GET'])
def get_number_bytes_received():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_receive_bytes_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)

@app.route('/collect_metrics/number_bytes_transmit', methods=['GET'])
def get_number_bytes_transmit():
    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    measurement_name = "container_network_transmit_bytes_total"
    data_frame = query_api.query_data_frame(f'from(bucket:"{bucket}") '
                                            f'|> range(start: {start}) '
                                            f'|> filter(fn: (r) => r["_measurement"] == "{measurement_name}") ' 
                                            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                                            '|> keep(columns: ["interface", "counter"])')

    unique_val_table = len(pd.unique(data_frame['table']))
    unique_in = pd.unique(data_frame['interface'])

    #print(unique_val_table, unique_in)
    
    list_df = []
    for i in range(unique_val_table):
        list_df.append(data_frame[data_frame['table'] == i])
    avg_number_packets_per_interface = {}
    for df in list_df:
        values = df["counter"].tolist()
        unique_in = pd.unique(df['interface'])
        mean_values = mean(values)
        #print("SOU A UNIQUE INTERFACE", unique_in, mean_values)
        avg_number_packets_per_interface[unique_in[0]] = mean_values.to_json()
    
    return jsonify(avg_number_packets_per_interface)


'''
#############################################################################################################################################################################
#LOGS

@app.route('/collect_logs/all_logs', methods=['GET'])
@jwt_required()
def get_all_logs():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')

    query = f'from(bucket: "{bucket_logs}") |> range(start: {start}) |> filter(fn: (r) => r["_field"] == "log")'

    result = query_api.query(query, org=INFLUXDB_ORG)

    dict_overall = {}

    if len(result) > 0:
        for table in result:
            list_dict = []
            for record in table.records:
                timestamp = record.get_time()
                log_content = record.get_field()
                value = record.get_value()
                measurement = record.get_measurement()
                dict = {}

                dict["timestamp"] = (str(timestamp)).to_json()
                dict["log_content"] = (str(log_content)).to_json()
                dict["value"] = (str(value)).to_json()
                list_dict.append(dict)
            dict_overall[measurement] =  list_dict.to_json()

    return jsonify(dict_overall)

@app.route('/collect_logs/specific_logs', methods=['GET'])
@jwt_required()
def get_specific_logs():

    start = request.args.get('start', '-10m')
    stop = request.args.get('stop', 'now')
    name = request.args.get('name', '')
    
    if name:
        name = "filelogs_" + str(name)


        query = f'from(bucket: "{bucket_logs}") |> range(start: {start}) |> filter(fn: (r) => r["_measurement"] == "{name}") |> filter(fn: (r) => r["_field"] == "log")'

        result = query_api.query(query, org=INFLUXDB_ORG)

        if len(result) > 0:
            list_dict = []
            for table in result:
                for record in table.record:
                    timestamp = record.get_time()
                    log_content = record.get_field()
                    value = record.get_value()
                    dict = {}
                    dict["timestamp"] = str(timestamp).to_json()
                    dict["log_content"] = str(log_content).to_json()
                    dict["value"] = str(value).to_json()
                    list_dict.append(dict)

        return jsonify(list_dict)
    
    return -1

###################################################################################################################################################################
#AUX FUNCTIONS
def calculate_avg_delay(rows):
    list_vals = []
    for i in range(len(rows)):
        if i != 0:
            val = (rows[i] - rows[i-1]).total_seconds()
            list_vals.append(val)
    return mean(list_vals) if len(list_vals) > 1 else -1

def get_curr_unix_time():
    current_unix_time = int(time.time())
    #print("Current Unix time:", current_unix_time)
    return current_unix_time

def get_x_time_ago_unix_time(x):
    current_unix_time = get_curr_unix_time()
    unix_time_10_min_ago = current_unix_time - x * 60  # 10 minutes * 60 seconds/minute
    #print("Unix time 10 minutes ago:", unix_time_10_min_ago)
    return unix_time_10_min_ago
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010)