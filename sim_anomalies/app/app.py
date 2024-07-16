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

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sys
import os
import signal
import requests
import yaml
import logging
import docker
import subprocess
import time
import threading
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from prometheus_api_client import PrometheusConnect, MetricSnapshotDataFrame, MetricRangeDataFrame
import pandas as pd
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_httpauth import HTTPTokenAuth
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pyshark
import time
import subprocess
import re
import asyncio
import struct
import socket
import random
import time
import signal
import sys
###############################################################################################################

aux = 0
max_cores = 3
max_seconds = 90
stress_process = None
ip_and_mask = None

def generate_random_cpu_cores():
    return random.randint(1, max_cores)
def generate_random_seconds():
    return random.randint(20, max_seconds)

def run_stress():
    global stress_process
    cores = generate_random_cpu_cores()
    seconds = generate_random_seconds()
    command = f"stress --cpu {cores} --timeout {seconds}s"
    print("GOING TO EXECUTE THIS COMMAND", command, flush=True)
    stress_process = subprocess.Popen(command, shell=True)
    stress_process.wait()
    stress_process = None
    #subprocess.run(command, shell=True)
    print("Ran stress command", flush=True)

def block_ip():
    
    seconds = generate_random_seconds()
    ip_mask = find_ip()
    command = f"iptables -A INPUT -s {ip_mask} -j DROP"
    print("GOING TO EXECUTE THIS COMMAND", command, flush=True)
    subprocess.run(command, shell=True)
    print(f"Blocked IP: {ip_mask}", flush=True)
    time.sleep(seconds)
    unblock_ip(ip_mask)

def unblock_ip(ip_mask):
    command = f"iptables -D INPUT -s {ip_mask} -j DROP"
    print("GOING TO EXECUTE THIS COMMAND", command, flush=True)
    subprocess.run(command, shell=True)
    print(f"Unblocked IP: {ip_mask}", flush=True)

def cleanup(signum, frame):
    global ip_and_mask, stress_process
    print("Caught signal, cleaning up...", flush=True)
    if ip_and_mask:
        unblock_ip(ip_and_mask)
    if stress_process and stress_process.poll() is None:
        stress_process.terminate()
        stress_process.wait()
    sys.exit(0)

def find_ip():
    client = docker.from_env()
    container_id = socket.gethostname()
    print("SOu o container id", container_id, flush=True)
    container = client.containers.get(container_id)
    print("SOU o container", container, flush=True)
    network_settings = container.attrs['NetworkSettings']['Networks']
    print("Sou as netwokr settings", network_settings, flush=True)
    net = network_settings['service_network']
    ip = net['IPAddress']
    print("Sou o ip", ip, flush=True)
    prefix_len = net['IPPrefixLen']

    mask = (0xffffffff >> (32 - prefix_len)) << (32 - prefix_len)
    subnet_mask = socket.inet_ntoa(struct.pack(">I", mask))

    return f"{ip}/{subnet_mask}"
    

    
def main():
    global ip_and_mask
    print("entro no main", flush=True)
    ip_and_mask = find_ip()
    print(f"Container ip and mask is: {ip_and_mask}", flush=True)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    #print("entro no main", flush=True)
    events = ['normal'] * 288 + ['anomalous'] * 72
    random.shuffle(events)

    for event in events:
        #find_ip()
        if event == 'normal':
            print("Performing normal operation", flush=True)
        else:
            print("vou ser anomalous", flush=True)
            action = random.choice(['stress', 'block_ip'])
            if action == 'stress':
                run_stress()
            else:
                block_ip()
        time.sleep(random.uniform(25, 35))

if __name__ == '__main__':
    main()