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
import schedule
import tarfile

#import psutil
####################################################################################################
####################################################################################################
####################################################################################################

#-------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#GLOBAL VARIABLES

interface_threads = {}
pre_selected_threads = []
interface_threads_aux = []
curr_interfaces = []
main_threads = {}
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
login_manager = LoginManager(app)
#jwt = JWTManager(app)
#auth = HTTPTokenAuth(scheme='Bearer')
class User(UserMixin):
    pass
#users = {
 #   'user':'pass',
#}
#Define variables - files and endpointsr
options_file = 'options.txt'
selected_options_file = 'selected_options.txt'
jobs_file = 'aux.txt'
prometheus_container_name = 'prometheus'
prometheus_config_file = '/app/prometheus/prometheus.yml'
prometheus_url = 'http://localhost:9090'
prometheus_reload = "http://localhost:9090/-/reload"
fluentbit_reload = "http://localhost:2020/api/v2/reload"
packet_cache = {}
packet_cache_times = {}
cache_lock = threading.Lock()
influxdb_ip = ""


CONTAINER_NAME = "influxdb"
BACKUP_DIR = "/backups"


#Define client to interact with docker containers
client = docker.from_env()
#Function to load the uiser

class DynamicCapture:
    def __init__(self, batch_size=300):
        self.interfaces = self.get_active_interfaces()
        self.interfaces_to_capture = self.get_active_interfaces_no_monitor()
        self.capture_thread = None
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.capture_stop_event = threading.Event()
        self.aux = 0
        self.packet_list =[]
        self.batch_size = batch_size
        self.first_monitor = 0
        self.networks_not_to_monitor = []

    def get_active_interfaces(self):
        ip_a_output = subprocess.check_output(['ip', 'a']).decode('utf-8')
        output_list = separate_input(ip_a_output)
        networks_names = extract_strings(output_list)
        networks_names = remove_veth_strings(networks_names)
        return networks_names #, ip_addresses
    
    def get_active_interfaces_no_monitor(self):
        ip_a_output = subprocess.check_output(['ip', 'a']).decode('utf-8')
        output_list = separate_input(ip_a_output)
        networks_names = extract_strings(output_list)
        networks_names = remove_veth_strings(networks_names)
        not_monitor = self.read_selected_options_net()
        if not_monitor != []:
            for interface in not_monitor:
                if interface in networks_names:
                    networks_names.remove(interface)
        return networks_names #, ip_addresses

    def start_capture(self):
        self.capture_stop_event.clear()
        print(f'Starting capture on interfaces: {self.interfaces_to_capture}', flush=True)
        self.aux += 1
        while not self.capture_stop_event.is_set():
            #print("Quantas vezes entro asqui", flush=True)
            try:
                capture = pyshark.LiveCapture(interface=self.interfaces_to_capture)
                capture.sniff(packet_count=50)
                #print("aqui antes", flush=True)
                aux = 0
                #await capture.sniff_continuously(packet_count=5)
                for packet in capture:
                #for packet in capture:  # Adjust the timeout as needed
                    if self.capture_stop_event.is_set():
                        print("event is set", flush=True)
                        break
                    self.packet_list.append(packet)
                    # Process the packet here if needed
                    #print("here - ", aux, len(capture), type(capture), self.aux, flush=True)
                    if len(self.packet_list) >= self.batch_size:
                        print("flushing", flush=True)
                        self.flush_packets()
                    aux+=1
                    
            except Exception as e:
                print(f'Error capturing packets: {e}', flush=True)
            finally:
                capture.close()
                print('Capture stopped.', flush=True)
            time.sleep(1)

    def flush_packets(self):
        point_list = []
        global influxdb_ip
        token = "InfluxDBToken"
        org = "MyOrg"
        url = f"http://{influxdb_ip}:5007"
        client_influx = influxdb_client.InfluxDBClient(url=url, token=token, org=org, timeout=30_000)
        bucket = "Network"
        
        for packet in self.packet_list:
            packet_p = self.process_packet(packet)
            point_list.append(packet_p)
        self.packet_list = []

        #define write db options
        write_api = client_influx.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=bucket, org=org, record=point_list)
        #   Close the client
        client.close()

    def process_packet(self, packet):
        
        packet_id = ""
        packet_info = {
            "measurement": "packets",
            "tags": {},
            "fields": {
                "length": int(packet.length),
                "timestamp": packet.sniff_time.isoformat()
            },
            "time": packet.sniff_time.isoformat()
        }
        
        # Source and destination information
        if hasattr(packet, 'ip'):
            packet_info['tags']['src_ip'] = packet.ip.src
            packet_info['tags']['dst_ip'] = packet.ip.dst
            packet_id += "_" + str(packet_info['tags']['src_ip']) + "_" + str(packet_info['tags']['dst_ip'])

        if hasattr(packet, 'tcp'):
            packet_info['fields']['src_port'] = int(packet.tcp.srcport)
            packet_info['fields']['dst_port'] = int(packet.tcp.dstport)
            packet_info['tags']['protocol'] = 'TCP'
            packet_id += "_" + str(packet_info['tags']['protocol']) + "_" + str(packet_info['fields']['src_port']) + "_" + str(packet_info['fields']['dst_port'])

        elif hasattr(packet, 'udp'):
            packet_info['fields']['src_port'] = int(packet.udp.srcport)
            packet_info['fields']['dst_port'] = int(packet.udp.dstport)
            packet_info['tags']['protocol'] = 'UDP'
            packet_id += "_" + str(packet_info['tags']['protocol']) + "_" + str(packet_info['fields']['src_port']) + "_" + str(packet_info['fields']['dst_port'])

        elif hasattr(packet, 'icmp'):
            packet_info['fields']['icmp_type'] = int(packet.icmp.type)
            packet_info['fields']['icmp_code'] = int(packet.icmp.code)
            packet_info['tags']['protocol'] = 'ICMP'
            packet_id += "_" + str(packet_info['tags']['protocol']) + "_" + str(packet_info['fields']['icmp_type']) + "_" + str(packet_info['fields']['icmp_code'])


        elif hasattr(packet, 'igmp'):
            packet_info['tags']['protocol'] = 'IGMP'
            packet_id += "_" + str(packet_info['tags']['protocol'])

        elif hasattr(packet, 'sctp'):
            packet_info['fields']['src_port'] = int(packet.sctp.srcport)
            packet_info['fields']['dst_port'] = int(packet.sctp.dstport)
            packet_info['tags']['protocol'] = 'SCTP'
            packet_id += "_" + str(packet_info['tags']['protocol']) + "_" + str(packet_info['fields']['src_port']) + "_" + str(packet_info['fields']['dst_port'])

        else:
            packet_info['tags']['protocol'] = packet.transport_layer if hasattr(packet, 'transport_layer') else 'UNKNOWN'
            packet_id += "_" + str(packet_info['tags']['protocol'])
        # Additional fields
        if hasattr(packet, 'eth'):
            packet_info['fields']['src_mac'] = packet.eth.src
            packet_info['fields']['dst_mac'] = packet.eth.dst
            packet_id += "_" + str(packet_info['fields']['src_mac']) + "_" + str(packet_info['fields']['dst_mac'])


        packet_info['fields']['packet_id'] = packet_id
        #packet_info['fields']['packet_delay'] = self.measure_delay(packet=packet)

        return packet_info

    def start(self):
        self.capture_thread = threading.Thread(target=self.start_capture)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        interface_threads_aux.append(self.capture_thread)

        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self. monitor_thread = threading.Thread(target=self.monitor_interfaces)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            interface_threads_aux.append(self.monitor_thread)

    def stop(self):
        self.stop_event.set()
        if self.capture_thread:
            self.capture_stop_event.set()
            self.capture_thread.join()
        if self.monitor_thread:
            self.monitor_thread.join()

    def read_selected_options_net(self):
        try:
            with open("selected_options_net.txt", 'r') as file:
                lines = [line.strip() for line in file]
            return lines
        except FileNotFoundError:
            return []
    
    def monitor_interfaces(self):
        aux = 0
        while not self.stop_event.is_set():
            active_interfaces = self.get_active_interfaces()
            active_interfaces_to_capture = self.get_active_interfaces_no_monitor()
            #not_monitor_aux = self.read_selected_options_net()
            if self.first_monitor == 0:
                for interface in active_interfaces:
                    curr_interfaces.append(interface)
                self.first_monitor+=1
            #curr_interfaces = self.get_active_interfaces()
            if aux == 0:
                print(f'Monitoring', active_interfaces, active_interfaces_to_capture, flush=True)
                aux+=1
            with self.lock:
                if set(active_interfaces) != set(self.interfaces):
                    self.interfaces = active_interfaces
                    self.interfaces_to_capture = active_interfaces_to_capture
                    for interface in self.interfaces:
                        if interface not in curr_interfaces:
                            curr_interfaces.append(interface)
                    for interface in curr_interfaces:
                        if interface not in self.interfaces:
                            curr_interfaces.remove(interface)
                    print(f'Interfaces changed to: {self.interfaces}, and to capture: {self.interfaces_to_capture}', flush=True)
                    if self.capture_thread and self.capture_thread.is_alive():
                        self.capture_stop_event.set()
                        print("Waiting 15 seconds to restart capture")
                        time.sleep(15)
                        self.capture_thread = threading.Thread(target=self.start_capture)
                        self.capture_thread.daemon = True
                        self.capture_thread.start()
                        interface_threads_aux.append(self.capture_thread)
                else:
                    if set(active_interfaces_to_capture) != set(self.interfaces_to_capture):
                        self.interfaces = active_interfaces
                        self.interfaces_to_capture = active_interfaces_to_capture
                        for interface in self.interfaces:
                            if interface not in curr_interfaces:
                                curr_interfaces.append(interface)
                        for interface in curr_interfaces:
                            if interface not in self.interfaces:
                                curr_interfaces.remove(interface)
                        print(f'Interfaces changed to: {self.interfaces}, and to capturee: {self.interfaces_to_capture}', flush=True)
                        if self.capture_thread and self.capture_thread.is_alive():
                            self.capture_stop_event.set()
                            print("Waiting 15 seconds to restart capture")
                            time.sleep(15)
                            self.capture_thread = threading.Thread(target=self.start_capture)
                            self.capture_thread.daemon = True
                            self.capture_thread.start()
                            interface_threads_aux.append(self.capture_thread)
            #print("THREADS AUX", interface_threads_aux, curr_interfaces, flush=True)
            time.sleep(10)

###################################################################################################
###################################################################################################
###################################################################################################

#-------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#APP/INTERFACE FUNCTIONS/ENDPOINTS
@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

#cookie_name = 'cookie_name'
#Function to login before enter the UI
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'username' and password == 'password':
            user = User()
            user.id = 1
            login_user(user)
            return redirect(url_for('index'))
        
    return render_template('login.html')

#Function to logou the user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#Interface GET and POST function
@app.route('/', methods=['GET', 'POST'])
#@auth.login_required
#@jwt_required()
def index():
    global interface_threads
    #When there is a submit (POST)
    if request.method == 'POST':
        #Fetch selected options (metrics checked in the UI)
        selected_options = request.form.getlist('option')
        #Fetch selected jobs (jobs checked in the UI)
        selected_jobs = request.form.getlist('job')
        #Fetch selected metrics and associated jobs from the UI
        selected_jobs_by_option = {}
        for option in selected_options:
            selected_jobs_by_option[option] = request.form.getlist(f'job_{option}[]')
        selected_options_node = request.form.getlist('option_node')
        selected_options_logs = request.form.getlist('option_log')
        selected_options_net = request.form.getlist('option_net')
        #Save the selected options (metrics, jobs, and jobs associated to the metrics)
        save_selected_options(selected_jobs_by_option)
        save_selected_jobs(selected_jobs)
        save_selected_options_node(selected_options_node)
        save_selected_options_logs(selected_options_logs)
        save_selected_options_net(selected_options_net)
        #Based on the saved options, generate the prometheus config file 
        generate_prometheus_config()
        relabel_node_metrics_on_prometheus_config()
        #Ping the /-/reload endpoint of prometheus to check the configuration and reload it
        trigger_prometheus_reload()
        lista_logs, container_names_logs, endpoint_logs = get_container_logs_location()
        config = generate_fluent_bit_conf(lista_logs, container_names_logs)
        if config != -1:
            write_to_file(config)
            trigger_fluentbit_reload(endpoint_logs)
        else:
            config = generate_first_fluentbit(lista_logs, container_names_logs)
            write_to_file(config)
            trigger_fluentbit_reload(endpoint_logs)
        conf = generate_telegraf_conf(container_names_logs)
        write_telegraf_file(conf)
        restart_telegraf()
        #check_networks_not_monitor()

    if current_user.is_authenticated:
        aux_first = 0
        #Normal state/no submit (GET)
        #Read the options (metrics) to display in the UI
        options = read_options()
        #fetch all metric names being scraped by prometheus
        metric_names = get_all_metrics(prometheus_url)
        #iterate through all metric names
        metric_names = [item for item in metric_names if item.startswith('container')]
        if "container_scrape_error" in metric_names:
            metric_names.remove("container_scrape_error")

        node_metric_names = get_all_metrics(prometheus_url)
        node_metric_names = [item for item in node_metric_names if item.startswith('node')]
        #Fetch running containers info - names and ports
        container_names, container_ports, container_ips = give_container_name_ports_ip()
        #Insert option "all", to select all the options showed in the UI
        container_names.insert(0, 'all')
        #Strings to remove from the names list - prometheus and cadvisor are never presented in the UI, they are used for the metrics collection
        #Defining the names of the running containers as the jobs
        jobs = container_names
        options = metric_names
        options_node = node_metric_names
        options_logs = get_container_names()
        options_logs.insert(0, 'all')
        #Read options already selected (metrics and jobs (associated and not associated to the metrics))
        selected_jobs_by_option = read_selected_options()
        selected_jobs = read_selected_jobs()
        selected_options_node = read_selected_options_node()
        selected_options_logs = read_selected_options_logs()
        selected_options_net = read_selected_options_net()
        selected_options = []
        for string in selected_jobs_by_option:
            selected_options.append(string.split('/')[0])
        if aux_first == 0:
            pre_selected_threads=selected_options_net
            aux_first+=1
        #networks = list(interface_threads.keys())
        #networks+=pre_selected_threads
        print("PRE_SELECTED_THREADS", curr_interfaces, flush=True)
        networks = curr_interfaces#interface_threads_aux
        print("NETWORKS", networks, flush=True)
        print("AUX_THREADS", interface_threads_aux, flush=True)
        return render_template('index.html', options=options, selected_options=selected_options, selected_jobs_by_option=selected_jobs_by_option, options_node=options_node, selected_options_node=selected_options_node, options_logs=options_logs, selected_options_logs=selected_options_logs, networks=networks, selected_options_net=selected_options_net, jobs=jobs, selected_jobs=selected_jobs)
    return redirect(url_for('login'))

###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#READ AND SAVE FUNCTIONS FOR THE INTERFACE OPTIONS TO THE TXT FILES TO PERSIST SAVE

#Function that reads jobs from the jobs file
#Not being used?
def read_jobs():
    with open(jobs_file, 'r') as file:
        return [line.strip() for line in file]

#Function that read the options from the options file
#Not being used?
def read_options():
    with open(options_file, 'r') as file:
        return [line.strip() for line in file]

#Function that reads the selected options of the UI and returns a list and a dictionary if the file is not empty
#The list contains the metrics and jobs, and the dictionary the metrics with the associated jobs
def read_selected_options():
    try:
        with open(selected_options_file, 'r') as file:
            lines = [line.strip() for line in file]
        if lines:  
            result_dict = {}
            if lines != []:
                for item in lines:
                    key, value_str = item.split(":")
                    key = key.strip()
                    value_list = [val.strip() for val in value_str.split("/")]
                    result_dict[key] = value_list
                cleaned_dict = {key: [item for item in value if item] for key, value in result_dict.items()}
                return cleaned_dict
            else:
                return {}
        else:
            result_dict = {}
            return result_dict
    except FileNotFoundError:
        return []

#Function that stores the checked options (jobs, metrics, and associated jobs) from the ui
#The variables come from the post request on the index() function
#Stores them in the selected_options.txt file
def save_selected_options(selected_jobs_by_option):
    #Check if the variables are empty
    #If they are, writes a blank line on the .txt file
    if selected_jobs_by_option == {}:
            with open("selected_options.txt", "w") as file:
                file.write("")
    #If not, stores on the .txt file the checked metrics, places a delimiter, then the checked jobs, places another delimiter, and then the metrics with the associated jobs
    else:
        with open(selected_options_file, 'w') as file:
            for option in selected_jobs_by_option:
                file.write(option)
                file.write(": ")
                for job in selected_jobs_by_option[option]:
                    file.write(job)
                    file.write("/")
                file.write("\n")

def save_selected_options_node(selected_options_node):
    if selected_options_node == []:
        with open("selected_options_node.txt", "w") as file:
            file.write("")
    else:
        with open("selected_options_node.txt", "w") as file:
            file.write('\n'.join(selected_options_node))

def save_selected_jobs(selected_jobs):
    if selected_jobs == []:
        with open("selected_jobs.txt", "w") as file:
            file.write("")
    else:
        with open("selected_jobs.txt", "w") as file:
            file.write('\n'.join(selected_jobs))

def save_selected_options_logs(selected_options_logs):
    if selected_options_logs == []:
        with open("selected_options_logs.txt", "w") as file:
            file.write("")
    else:
        with open("selected_options_logs.txt", "w") as file:
            file.write('\n'.join(selected_options_logs))

def save_selected_options_net(selected_options_net):
    if selected_options_net == []:
        with open("selected_options_net.txt", "w") as file:
            file.write("")
    else:
        with open("selected_options_net.txt", "w") as file:
            file.write('\n'.join(selected_options_net))

def read_selected_jobs():
    try:
        with open("selected_jobs.txt", "r") as file:
            lines = [line.strip() for line in file]
        return lines
    except FileNotFoundError:
        return []

def read_selected_options_node():
    try:
        with open("selected_options_node.txt", 'r') as file:
            lines = [line.strip() for line in file]
        return lines
    except FileNotFoundError:
        return []

def read_selected_options_logs():
    try:
        with open("selected_options_logs.txt", 'r') as file:
            lines = [line.strip() for line in file]
        return lines
    except FileNotFoundError:
        return []

def read_selected_options_net():
    try:
        with open("selected_options_net.txt", 'r') as file:
            lines = [line.strip() for line in file]
        return lines
    except FileNotFoundError:
        return []

###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#PROMETHEUS RELATED FUNCTIONS

#Functions that recreates the prometheus container
#Currently not being used
def recreate_prometheus_container():
    try:
        prometheus_container = client.containers.get(prometheus_container_name)
        prometheus_container.stop()
        prometheus_container.remove()
        create_prometheus_container()
    except docker.errors.NotFound:
        create_prometheus_container()

#Function that creates the prometheus container
#Currently not being used
def create_prometheus_container():
    client.container.run(
        'prom/prometheus',
        detach=True,
        name=prometheus_container_name,
        volumes={prometheus_config_file: {'bind': '/etc/prometheus/prometheus.yml', 'mode': 'rw'}},
        ports={'9090/tcp': 9090},
        command=['--config.file=/etc/prometheus/prometheus.yml', '--web.enable-lifecycle'],
        network_mode='config_network'
    )

#Function to restart the prometheus container
#Currently not being used
def restart_prometheus():
    prometheus_container = client.containers.get('prometheus')
    prometheus_container.restart()

#Function that generates a new prometheus configuration based on the UI choices.
#If none of the options is checked in the UI, the configuration returns to the default one (as in the first start)
def generate_prometheus_config():
    #Commented example of hoe the first configuration looks
    #{'global': {'scrape_interval': '15s'}, 'scrape_configs': [{'job_name': 'prometheus', 'static_configs': [{'targets': ['prometheus:9090']}]}, {'job_name': 'service1', 'static_configs': [{'targets': ['service1:5000']}]}, {'job_name': 'cadvisor', 'static_configs': [{'targets': ['cadvisor:8080']}]}]}
    
    #File path of the prometheus config file inside the container
    file_path='/app/prometheus/prometheus.yml'
    #Fetch the data of the config file to the data variable
    with open(file_path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)

    #Variable with the default configuration of prometheus
    #Only presentes at first the prometheus and cadvisor
    #All the container metrics from all the containers are monitored in this config
    default_prom = {
        'global': {'scrape_interval': '15s'},
        'scrape_configs': [{'job_name': 'prometheus', 'static_configs': [{'targets': ['prometheus:9090']}]},
                           {'job_name': 'cadvisor', 'static_configs': [{'targets': ['cadvisor:8080']}]},
                           {'job_name': 'node-exporter', 'static_configs': [{'targets': ['node-exporter:9100']}]}]
    }

    #Call function that returns the selected options from the UI
    #This is the jobs to scrape, the metrics and its associated jobs not to be scraped
    jobs_dict = read_selected_options()
    selected_jobs = read_selected_jobs()
    #Check if the checked options are empty (nothing is selected in the UI when the submit button is hit)
    if jobs_dict != {}:

        new_selected_options = list(jobs_dict.keys())

        for scrape_config in data['scrape_configs']:
            if scrape_config.get('job_name')=='cadvisor':
                list_relabels = []
                for option in new_selected_options:
                    if "all" in jobs_dict[option]:
                        metrica = "("+option+")"
                        new_metric_relabel = {
                            'action': 'drop',
                            'source_labels': ['__name__'],
                            'regex': metrica
                        }
                        list_relabels.append(new_metric_relabel)
                    else:
                        if jobs_dict[option] != []:
                            for job in jobs_dict[option]:
                                metrica = option
                                new_metric_relabel = {
                                    'action': 'drop',
                                    'source_labels': ['__name__', 'container_label_com_docker_compose_service'],
                                    'regex': metrica+';'+job
                                }
                                list_relabels.append(new_metric_relabel)
                        else:
                            jobs_dict[option] = ["all"]
                            save_selected_options(jobs_dict)
                            metrica = "("+option+")"
                            new_metric_relabel = {
                                'action': 'drop',
                                'source_labels': ['__name__'],
                                'regex': metrica
                            }
                            list_relabels.append(new_metric_relabel)

                if 'metric_relabel_configs' not in scrape_config:
                    scrape_config['metric_relabel_configs'] = []
                    for relabel in list_relabels:
                        scrape_config['metric_relabel_configs'].insert(len(scrape_config['static_configs']), relabel)
                else:
                    removed_value = scrape_config.pop('metric_relabel_configs', None)
                    scrape_config['metric_relabel_configs'] = []
                    for relabel in list_relabels:
                        scrape_config['metric_relabel_configs'].insert(len(scrape_config['static_configs']), relabel) 
        
        with open('try.txt', 'w') as txt_file:
            yaml.dump(data, txt_file, default_flow_style=False)
        with open('try.txt', 'r') as txt_file:
            modified_data = yaml.safe_load(txt_file)
        with open('aux.yml', 'w') as yaml_file:
            yaml.dump(modified_data, yaml_file, default_flow_style=False)
        with open(file_path, 'w') as yaml_file:
            yaml.dump(modified_data, yaml_file, default_flow_style=False)                   

    else:
        if selected_jobs == []:
            generate_first_prometheus()
        else:
            containers, ports, ips = give_container_name_ports_ip()
            for container in containers:
                if container in selected_jobs:
                    index = containers.index(container)
                    port = str(ports[index])
                    for dictionary in ips:
                        # Check if the search key exists in the current dictionary
                        if container in dictionary:
                            # If found, print the corresponding value
                            ip = str(dictionary[container])
                            # If you only need the value associated with the first occurrence of the key,
                            # you can break the loop here
                            break
                    job_ = {'job_name': f'{str(container)}', 'static_configs': [{'targets': [f'{ip}:{port}']}]}
                    default_prom["scrape_configs"].append(job_)
            
            with open('try.txt', 'w') as txt_file:
                yaml.dump(default_prom, txt_file, default_flow_style=False)
            with open('try.txt', 'r') as txt_file:
                modified_data = yaml.safe_load(txt_file)
            with open('aux.yml', 'w') as yaml_file:
                yaml.dump(modified_data, yaml_file, default_flow_style=False)
            with open(file_path, 'w') as yaml_file:
                yaml.dump(modified_data, yaml_file, default_flow_style=False)

def generate_first_prometheus():
    file_path = '/app/prometheus/prometheus.yml'
    with open(file_path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)

    default_prom = {
        'global': {'scrape_interval': '15s'},
        'scrape_configs': [{'job_name': 'prometheus', 'static_configs': [{'targets': ['prometheus:9090']}]},
                           {'job_name': 'cadvisor', 'static_configs': [{'targets': ['cadvisor:8080']}]},
                           {'job_name': 'node-exporter', 'static_configs': [{'targets': ['node-exporter:9100']}]}]
    }
    with open('try.txt', 'w') as txt_file:
        yaml.dump(default_prom, txt_file, default_flow_style=False)
    with open('try.txt', 'r') as txt_file:
        modified_data = yaml.safe_load(txt_file)
    with open('aux.yml', 'w') as yaml_file:
        yaml.dump(modified_data, yaml_file, default_flow_style=False)
    with open(file_path, 'w') as yaml_file:
        yaml.dump(modified_data, yaml_file, default_flow_style=False) 

def relabel_node_metrics_on_prometheus_config():
    file_path = '/app/prometheus/prometheus.yml'
    with open(file_path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)

    selected_options_node = read_selected_options_node()
    if selected_options_node != []:
        for scrape_config in data['scrape_configs']:
            if scrape_config.get('job_name')=='node-exporter':
                list_relabels = []
                for option_node in selected_options_node:
                    metrica = "("+option_node+")"
                    new_metric_relabel = {
                        'action': 'drop',
                        'source_labels': ['__name__'],
                        'regex': metrica
                    }
                    list_relabels.append(new_metric_relabel)
                if 'metric_relabel_configs' not in scrape_config:
                    scrape_config['metric_relabel_configs']=[]
                    for relabel in list_relabels:
                        scrape_config['metric_relabel_configs'].insert(len(scrape_config['static_configs']), relabel)
                else:
                    removed_value = scrape_config.pop('metric_relabel_configs', None)
                    scrape_config['metric_relabel_configs']=[]
                    for relabel in list_relabels:
                        scrape_config['metric_relabel_configs'].insert(len(scrape_config['static_configs']), relabel)
        with open('try.txt', 'w') as txt_file:
            yaml.dump(data, txt_file, default_flow_style=False)
        with open('try.txt', 'r') as txt_file:
            modified_data = yaml.safe_load(txt_file)
        with open('aux.yml', 'w') as yaml_file:
            yaml.dump(modified_data, yaml_file, default_flow_style=False)
        with open(file_path, 'w') as yaml_file:
            yaml.dump(modified_data, yaml_file, default_flow_style=False) 
    else:
        for scrape_config in data['scrape_configs']:
            if scrape_config.get('job_name')=='node-exporter':
                removed_value = scrape_config.pop('metric_relabel_configs', None)
        with open('try.txt', 'w') as txt_file:
            yaml.dump(data, txt_file, default_flow_style=False)
        with open('try.txt', 'r') as txt_file:
            modified_data = yaml.safe_load(txt_file)
        with open('aux.yml', 'w') as yaml_file:
            yaml.dump(modified_data, yaml_file, default_flow_style=False)
        with open(file_path, 'w') as yaml_file:
            yaml.dump(modified_data, yaml_file, default_flow_style=False) 

#Function that triggers the prometheus hot reload functionality
#Ir reloads prometheus config if the configuration file is changed without ant restart of the container
#Sends a post request to the prometheus_reload variabel - endpoint /-/reload
def trigger_prometheus_reload():
    try:
        response = requests.post(prometheus_reload)
        response.raise_for_status()
        print('Prometheus reload initialized successfully!', flush=True)
    except requests.exceptions.RequestException as e:
        print(f'Error triggering Prometheus reload: {e}', flush=True)

#Function that connects with prometheus via prometheus api
#If no error, returns a list with all the metric names
def get_all_metrics(prometheus_url):
    metric_names_url = f"{prometheus_url}/api/v1/label/__name__/values"

    response = requests.get(metric_names_url)

    if response.status_code == 200:
        metric_names_data = response.json()
        return metric_names_data['data']
    else:
        print(f"Error: Unable to fetch metric names. Status code: {response.status_code}")
        return None

#Aux function that receives a query from prometheus and returns the result    
def query_prometheus(api_url, query):
    params = {'query': query}
    response = requests.get(f'{api_url}/api/v1/query', params=params)
    data = response.json()

    if response.status_code == 200:
        return data['data']['result']
    else:
        print(f'Error querying Prometheus: {data}')
        return None

###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#FLUENTBIT RELATED FUNCTIONS

#Function to reload fluentbit
def trigger_fluentbit_reload(endpoint):
    try:
        response = requests.post(endpoint)
        response.raise_for_status()
        print('Fluent-Bit reload initialized successfully!', flush=True)
    except requests.exceptions.RequestException as e:
        print(f"Error triggering Fluent-Bit reload: {e}", flush=True)
#FLUENTBIT PART
def generate_fluent_bit_conf(inputs, container_names_for_logs):
    global influxdb_ip
    config_template = """
[SERVICE]
    HTTP_Server On
    HTTP_Listen 0.0.0.0
    HTTP_PORT   2020
    Hot_Reload  On
{inputs}
[OUTPUT]
    Name        influxdb
    Match       *
    Host        {influxdb_ip}
    Port        5007
    Bucket      Second_Logs
    Org         MyOrg
    http_token InfluxDBToken
    sequence_tag    _seq
"""
    input_section_template = """
[INPUT]
    Name        tail
    Path        {path}
    tag         {tag}
"""
    selected_names = read_selected_options_logs()
    names = container_names_for_logs
    inputs_final = []
    names_final = []
    if selected_names != [] and "all" in selected_names:
        for i in range(len(names)):
            if names[i] == "fluent-bit" or names[i] == "influxdb":
                names_final.append(names[i])
                inputs_final.append(inputs[i])
    else:
        for i in range(len(names)):
            if selected_names != []:
                if names[i] not in selected_names:
                    names_final.append(names[i])
                    inputs_final.append(inputs[i])
            else:
                return -1
    inputs_str = "\n".join(input_section_template.format(path=path, tag=f"filelogs_{name}") for name, path in zip(names_final, inputs_final))
    return config_template.format(inputs=inputs_str, influxdb_ip=influxdb_ip)

def generate_first_fluentbit(inputs, container_names_for_logs):
    global influxdb_ip
    config_template = """
[SERVICE]
    HTTP_Server On
    HTTP_Listen 0.0.0.0
    HTTP_PORT   2020
    Hot_Reload  On
{inputs}
[OUTPUT]
    Name        influxdb
    Match       *
    Host        {influxdb_ip}
    Port        5007
    Bucket      Second_Logs
    Org         MyOrg
    http_token InfluxDBToken
    sequence_tag    _seq
"""
    input_section_template = """
[INPUT]
    Name        tail
    Path        {path}
    tag         {tag}
"""
    names = container_names_for_logs
    inputs_final = []
    names_final = []
    for i in range(len(names)):
        names_final.append(names[i])
        inputs_final.append(inputs[i])
    inputs_str = "\n".join(input_section_template.format(path=path, tag=f"filelogs_{name}") for name, path in zip(names_final, inputs_final))
    return config_template.format(inputs=inputs_str, influxdb_ip=influxdb_ip)

#REDO FLUENTBIT CONFIG FILE
def write_to_file(config_content, filename='/app/fluent-bit/fluent-bit.conf'):
    with open(filename, 'w') as f:
        f.write(config_content)


###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#FUNCTIONS RELATED TO SENDING THE NETWORK METREICS TO THE DATABASE
def capture_from_interfaces(interfaces):
    global pre_selected_threads
    aux = 0
    if aux == 0:
        pre_selected_threads = read_selected_options_net()
        aux+=1
    for interface in interfaces:
        if interface not in pre_selected_threads:
            stop_event = threading.Event()
            thread = threading.Thread(target=capture_packets, args=(interface, stop_event), daemon=True)
            interface_threads[interface] = (thread, stop_event)
            thread.start()

def get_ip_address(container):
    container_id = container.id
    container_name = container.name

    networks = container.attrs['NetworkSettings']['Networks']
    for network_name, network_details in networks.items():
        if network_details.get('Gateway'):
            bridge_network_name = network_name
            ip_address = network_details.get('IPAddress', 'N/A')

            return ip_address

#Returns a list of lists of strings. Each list of strings is information related to a network
def separate_input(input_text):
    lines = input_text.split('\n')
    result = []
    list_indexes = []
    cont_aux = 0
    for line in lines:
        result1 = starts_with_integer_and_colon(line)
        if result1==True:
            list_indexes.append(cont_aux)
            cont_aux+=1
        else:
            cont_aux+=1

    for i in range(len(list_indexes)):
        if i < len(list_indexes)-1:
            result.append(lines[list_indexes[i]:list_indexes[i+1]])
        else:
            result.append(lines[list_indexes[i]:])

    return result

#Returns the name of each network
def extract_strings(list_of_lists):
    extracted_strings = []
    for sublist in list_of_lists:
        if sublist:
            first_string = sublist[0]
            first_colon_index = first_string.find(":")
            second_colon_index = first_string.find(":", first_colon_index+1)
            if first_colon_index != -1 and second_colon_index != -1:
                extracted_string = first_string[first_colon_index + 1:second_colon_index]
                extracted_strings.append(extracted_string.strip())
    return extracted_strings 

#Remove the networks that start with veth in the name
def remove_veth_strings(string_list):
    return [s for s in string_list if not s.startswith("veth")]

#Returns the strings where the ip v4 are
def extract_ip_numbers(list_of_lists):
    list_of_thirds = []
    for list in list_of_lists:
        list_of_thirds.append(list[2].strip())
    return list_of_thirds

#Gets all the ip 
def get_ip(string_list):
    ip_addresses = []
    ip_regex = r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b'
    for string in string_list:
        matches = re.findall(ip_regex, string)
        ip_addresses.extend(matches)

    return ip_addresses

def capture_packets(network, stop_event):
    global influxdb_ip
    token = "InfluxDBToken"
    org = "MyOrg"
    url = f"http://{influxdb_ip}:5007"

    list_packet_sizes = []
    list_packet_sizes_tcp = []
    list_packet_sizes_udp = []
    time.sleep(10)
    capture = pyshark.LiveCapture(network.split("@")[0])
    client_influx = influxdb_client.InfluxDBClient(url=url, token=token, org=org, timeout=30_000)
    bucket = "Network"
    #define write db options
    write_api = client_influx.write_api(write_options=SYNCHRONOUS)
    for packet in capture.sniff_continuously():
        if stop_event.is_set():
            break

        id, packet_type  = generate_packet_id(packet)
        if id != -1:
            packet_delay = measure_delay(packet)
            packet_size = int(packet.length)
            packet_type = str(packet_type)
            if len(list_packet_sizes) >= 100:
                list_packet_sizes = list_packet_sizes[1:]
            name = "packet_sizes"
            interface = network
            packet_id = id 
            value = packet_size
            _now = datetime.utcnow()
            write_api.write(bucket, org, Point(name).tag("packet_id", packet_id).tag("packet_type", packet_type).tag("interface", interface).field("size", int(value)).time(_now))
            list_packet_sizes.append(packet_size)
            avg_packet_size = sum(list_packet_sizes)/len(list_packet_sizes)
            name = "avg_packet_sizes"
            value = avg_packet_size
            _now = datetime.utcnow()
            write_api.write(bucket, org, Point(name).tag("interface", interface).field("avg_size", float(value)).time(_now))
            #save tcp and udp separate
            if packet_type == "TCP":
                if len(list_packet_sizes_tcp) == 100:
                    list_packet_sizes_tcp = list_packet_sizes_tcp[1:]
                list_packet_sizes_tcp.append(packet_size)
                avg_packet_size_tcp = sum(list_packet_sizes_tcp)/len(list_packet_sizes_tcp)
                name = "avg_packet_sizes_tcp"
                value = avg_packet_size_tcp
                _now = datetime.utcnow()
                write_api.write(bucket, org, Point(name).tag("interface", interface).field("avg_size_tcp", float(value)).time(_now))
                name = "packet_sizes_tcp"
                _now = datetime.utcnow()
                value = packet_size
                write_api.write(bucket, org, Point(name).tag("packet_id", packet_id).tag("packet_type", packet_type).tag("interface", interface).field("size_tcp", int(value)).time(_now))
            if packet_type == "UDP":
                if len(list_packet_sizes_udp) == 100:
                    list_packet_sizes_udp = list_packet_sizes_udp[1:]
                list_packet_sizes_udp.append(packet_size)
                avg_packet_size_udp = sum(list_packet_sizes_udp)/len(list_packet_sizes_udp)
                name = "avg_packet_sizes_udp"
                value = avg_packet_size_udp
                _now = datetime.utcnow()
                write_api.write(bucket, org, Point(name).tag("interface", interface).field("avg_size_udp", float(value)).time(_now))
                name = "packet_sizes_udp"
                _now = datetime.utcnow()
                value = packet_size
                write_api.write(bucket, org, Point(name).tag("packet_id", packet_id).tag("packet_type", packet_type).tag("interface", interface).field("size_udp", int(value)).time(_now))
            name = "packet_delays"
            value = packet_delay
            _now = datetime.utcnow()
            write_api.write(bucket, org, Point(name).tag("packet_id", packet_id).tag("packet_type", packet_type).tag("interface", interface).field("packet_delay", value).time(_now))

def generate_packet_id(packet):
    if 'IP' in packet:
        ip_layer = packet['IP']
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
    elif 'IPv6' in packet:
        ipv6_layer = packet['IPv6']
        src_ip = ipv6_layer.src
        dst_ip = ipv6_layer.dst
    else:
        # Packet doesn't contain IP or IPv6 layer
        return -1, -1
    if 'TCP' in packet:
        tcp_layer = packet['TCP']
        src_port = tcp_layer.srcport
        dst_port = tcp_layer.dstport
        sequence_number = tcp_layer.seq_raw
        timestamp = datetime.now().timestamp()
        packet_id = f"{src_ip}_{src_port}_{dst_ip}_{dst_port}_{sequence_number}_{timestamp}"
        packet_type = "TCP"
    elif 'UDP' in packet:
        udp_layer = packet['UDP']
        src_port = udp_layer.srcport
        dst_port = udp_layer.dstport
        timestamp = datetime.now().timestamp()
        packet_id = f"{src_ip}_{src_port}_{dst_ip}_{dst_port}_{timestamp}"
        packet_type = "UDP"
    else: 
        return -1, -1
    #packet_id = f"{src_ip}_{src_port}_{dst_ip}_{dst_port}_{sequence_number}_{timestamp}"
    return packet_id, packet_type

def measure_delay(packet):
    #Extract transmit and receive timestamps from the packet
    transmit_time = packet.sniff_time.replace(tzinfo=timezone.utc)
    receive_time = datetime.now(timezone.utc)
    # Calculate the delay between transmit and receive timestamps
    delay = receive_time - transmit_time
    delay = delay.total_seconds()
    # Print or log the delay
    return delay

#CHeck if the string starts with a number followed by ":"
def starts_with_integer_and_colon(s):
    pattern = re.compile(r'^\d+:')
    return bool(pattern.match(s))

def compare_lists(list1, list2):
    #0 = added and removed
    #1 = added
    #2 = removed
    #3 = equal lists 
    set1 = set(list1)
    set2 = set(list2)

    added = set2 - set1
    removed = set1 - set2

    if added and removed:
        return added, removed, 0
    elif added:
        return added, -1, 1
    elif removed:
        return -1, removed, 2
    else:
        return -1, -1, 3

def stop_capture(interface):
    thread, stop_event = interface_threads.get(interface, (None, None))
    if thread:
        stop_event.set()
        #thread.join()

def start_capture(interface):
    """
    Function to start a capture thread for a given interface.
    
    :param interface: Interface identifier for which to start the thread.
    """
    print("Interface to start capturing = ", interface, flush=True)
    thread, stop_event = interface_threads.get(interface, (None, None))

    if thread and not thread.is_alive():
        # Reset the stop event in case it was previously set
        stop_event.clear()
        # Start the thread
        thread.start()
        print("Recomecei a dar capture da interface", interface, flush=True)
    elif thread:
        print("Thread already running for this interface.", flush=True)
    else:
        print("No thread found for this interface.", flush=True)

def check_networks_not_monitor():
    global pre_selected_threads
    interfaces_list = []
    selected_networks = read_selected_options_net()
    if pre_selected_threads != [] and pre_selected_threads != selected_networks:
        aux_pre_selected_threads = pre_selected_threads.copy()
        for thread in pre_selected_threads:
            if thread not in selected_networks:
                interfaces_list.append(thread)
                aux_pre_selected_threads.remove(thread)
        if interfaces_list != []:
            capture_from_interfaces(interfaces_list)
            pre_selected_threads = aux_pre_selected_threads.copy()
    if selected_networks != []:
        for net in selected_networks:
            stop_capture(net)
            old_thread, stop_event = interface_threads.pop(net, (None, None))
            pre_selected_threads.append(net)
    #print("SAIO DA FUNCAO", flush=True)

###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
#TELEGRAF
def generate_telegraf_conf(container_names_for_logs):
    file_path = '/app/telegraf/telegraf.conf'
    global influxdb_ip

    config_template = """
[[inputs.prometheus]]
  urls = ["http://cadvisor:8080/metrics"]
{processors_cadvisor}
[[outputs.influxdb_v2]]
  urls = ["http://{ip}:5007"]
  token = "InfluxDBToken"
  organization = "MyOrg"
  bucket = "cadvisor_bucket"
  namepass = ["container_*"]

[[inputs.prometheus]]
  urls = ["http://node-exporter:9100/metrics"]

[[outputs.influxdb_v2]]
  urls = ["http://{ip}:5007"]
  token = "InfluxDBToken"
  organization = "MyOrg"
  bucket = "node-exporter_bucket"
  namepass = ["node_*"]
  {node_metrics}
"""

    input_section_template = """
[[processors.filter]]
  namepass = {metrics_measurements}
  default = "pass"
  [[processors.filter.rule]]
    tags = {tags}
    action = "drop"
"""

    jobs_dict = read_selected_options()
    options_node = read_selected_options_node()
    
    if not jobs_dict and not options_node:
        return config_template.format(processors_cadvisor="", ip=influxdb_ip, node_metrics="")
    
    print("ESTOU NO GENERATE TELEGRAF", flush=True)
    processors_list = []
    
    if jobs_dict:
        print("ENTRO NO IF", flush=True)
        for option, names in jobs_dict.items():
            if "all" in names:
                tags_string = '{"name" = [' + ', '.join(f'"{tag}"' for tag in container_names_for_logs) + ']}'
                metrics_measurement = f'["{option}"]'
            else:
                tags_string = '{"name" = [' + ', '.join(f'"{name}"' for name in names) + ']}'
                metrics_measurement = f'["{option}"]'
            
            formatted_section_final = input_section_template.format(metrics_measurements=metrics_measurement, tags=tags_string)
            processors_list.append(formatted_section_final)
        processors = "\n".join(processors_list) if processors_list else ""
    else:
        processors = ""
    options_str = 'namedrop = [' + ', '.join(f'"{option}"' for option in options_node) + ']' if options_node else ''

    
    return config_template.format(processors_cadvisor=processors, ip=influxdb_ip, node_metrics=options_str)

def restart_telegraf():
    telegraf_container = client.containers.get('telegraf')
    telegraf_container.restart()

def write_telegraf_file(conf, filename='/app/telegraf/telegraf.conf'):
    with open(filename, 'w') as f:
        f.write(conf) 

###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#OTHER FUNCTIONS - GENERAL FUNCTIONS/ TEST FUNCTIONS

#FInd value by key in dictionary
def find_value_by_key(key, dict_list):
    for dictionary in dict_list:
        if key in dictionary:
            return dictionary[key]
    return None

#Function that extracts information about the containers. 
# Returns two lists - one with the container names, the other with the containers ports 
#(only adds to the lists the names and ports of the containers that expose ports to be scraped)
#the indexes of the two lists match the name of a specific container and its port
def give_container_name_ports_ip():
    #Calls the function that returns the informations about the containers
    running_containers = get_running_containers()
    #Define the lists for the containers names and ports
    container_names = []
    container_ports = []
    container_ip_addresses = []

    #Iterate through the containers and when the container has an exposed port, adds its name to the 
    #container_names list and its port to the container_ports list (in the same index)
    for container in running_containers:
        aux_list = []
        ports = container.attrs['NetworkSettings']['Ports']
        container_info = container.attrs
        network_settings = container_info['NetworkSettings']

        networks = network_settings['Networks']

        for network_name, network_info in networks.items():
            ip_address = network_info['IPAddress']

            container_ip_addresses.append({container.name:ip_address})
        
        for port_info in ports.keys():
            host_port_info = ports[port_info]
            if host_port_info is not None:
                host_port = host_port_info[0]['HostPort']
                container_ports.append(host_port)
                container_names.append(container.name)
    return container_names, container_ports, container_ip_addresses

#Fetch running containers function
def get_running_containers():
    client = docker.from_env()
    return [container for container in client.containers.list()]

def get_container_names():
    containers = get_running_containers()
    lista_container_names = []
    for container in containers:
        lista_container_names.append(container.name)
    return lista_container_names

def get_container_logs_location():
    running_containers = get_running_containers()
    lista_logs = []
    endpoint_ip = ""
    container_names = []

    for container in running_containers:
        container_info = container.attrs
        log_path = container_info['LogPath']
        lista_logs.append(log_path)
        container_names.append(container.name)

        network_settings = container_info['NetworkSettings']
        networks = network_settings['Networks']
        for network_name, network_info in networks.items():
            ip_address = network_info['IPAddress']
            if container.name == "fluent-bit":
                endpoint_ip = str(ip_address)
    endpoint = "http://"+endpoint_ip+":2020/api/v2/reload"
    return lista_logs, container_names, endpoint

def find_interface_by_ip(ip_address):
    ip_a_output = subprocess.check_output(['ip', 'a']).decode('utf-8')

    match = re.search(r'(?<=inet\s{})\s[^/]+'.format(re.escape(ip_address)), ip_a_output)
    if match:
        return match.group().strip()

###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################
#TELEGRAF PART



###################################################################################################
###################################################################################################
###################################################################################################

#------------------------------------------------------------------------------------------------#

###################################################################################################
###################################################################################################
###################################################################################################

#THREADS OF THE UI AND CREATION OF DB BUCKETS
def get_org_id():
    #from influxdb_client import InfluxDBClient
    global influxdb_ip
    # Configuration
    #url = 'http://localhost:5007'  # Adjust the port if different in your setup
    url = f"http://{influxdb_ip}:5007"
    token = 'InfluxDBToken'  # Replace with your actual admin token
    org = 'MyOrg'  # Your organization name

    # Create a client and query for organization details
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        # Fetch organizations and print their IDs
        orgs = client.organizations_api().find_organizations()
        for organization in orgs:
            print(f"Organization: {organization.name}, ID: {organization.id}")
            if org == organization.name:
                return organization.id
    finally:
        client.close()
    return -1

def create_bucket(name):
    global influxdb_ip
# Set your InfluxDB API token and organization ID
    INFLUX_TOKEN = "InfluxDBToken"
    #NEEDS TO BE DEFINED
    INFLUX_ORG_ID = get_org_id()

    if INFLUX_ORG_ID != -1:
        # Define the URL
        #url = "http://localhost:5007/api/v2/buckets"
        url = f"http://{influxdb_ip}:5007/api/v2/buckets"
        # Set the headers
        headers = {
            "Authorization": f"Token {INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

        # Define the payload
        payload = {
            "orgID": INFLUX_ORG_ID,
            "name": name,
            "retentionRules": [
                {
                    "type": "expire",
                    "everySeconds": 0,
                    "shardGroupDurationSeconds": 0
                }
            ]
        }

        # Send the POST request
        response = requests.post(url, json=payload, headers=headers)

        # Check the response status
        if response.status_code == 201:
            print("Bucket created successfully.")
        else:
            print("Failed to create bucket. Status code:", response.status_code)
            print("Response:", response.text)
    else:
        print("ORG ID FAILED", flush=True)

def load_influxdb_ip():
    try:
        with open("/app/ips.txt", "r") as file:
            lines = [line.strip() for line in file]
        if len(lines)>1:
            #to do
            pass
        else:
            ip = lines[0].split("=")[1]
        return ip
    except FileNotFoundError:
        return []

#Backups for influxdb
#to restore -influx restore /backups/directory

def execute_influxdb_backup(client, container_name, backup_dir):
    command = f"influx backup {backup_dir} --token InfluxDBToken"
    try:
        response = client.containers.run(container_name, command)
        print(response.decode('utf-8'), flush=True)
        print("passei", flush=True)
    except docker.errors.APIError as e:
        print(f"Error executing command in container {container_name}: {e}")

def compress_backup(backup_dir):
    backup_filename = f"backup-{datetime.now().strftime('%Y-%m-%d')}.tar.gz"
    with tarfile.open(os.path.join(backup_dir, backup_filename), "w:gz") as tar:
        tar.add(backup_dir, arcname=os.path.basename(backup_dir))

def delete_old_backups(backup_dir, days_to_keep=7):
    for file in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, file)
        if os.path.isfile(file_path) and file.startswith("backup-") and file.endswith(".tar.gz"):
            file_date = datetime.strptime(file[7:17], '%Y-%m-%d')
            if datetime.now() - file_date > timedelta(days=days_to_keep):
                os.remove(file_path)
                print(f"Deleted old backup: {file}")

def run_backup_script():
    os.system('/app/backup_script.sh')
    print("done", flush=True)
    compress_backup(BACKUP_DIR)
    delete_old_backups(BACKUP_DIR)

def perform_backup():
    client = docker.from_env()
    
    # Execute InfluxDB backup command inside the container
    execute_influxdb_backup(client, CONTAINER_NAME, BACKUP_DIR)
    print("feito", flush=True)
    # Compress backup
    
    
    # Delete old backups (older than 30 days)

def schedule_backup():
    # Schedule the backup to run every hour
    #schedule.every().hour.do(perform_backup)
    run_backup_script()
    schedule.every(7).days.do(run_backup_script)
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)


influxdb_ip = load_influxdb_ip()

#create_bucket("Final")
#create_bucket("Final_Node")
create_bucket("Network")
create_bucket("cadvisor_bucket")
create_bucket("node-exporter_bucket")
#TELEGRAF
print("VOU ALTERAR O TELEGRAF CONFIG", flush=True)
lista_logs_first, container_names_logs_first, endpoint_logs_first = get_container_logs_location()
conf = generate_telegraf_conf(container_names_logs_first)
write_telegraf_file(conf)
restart_telegraf()
print("ALTEREI  TELEGRAF CONFIG", flush=True)

dynamic_capture = DynamicCapture()
dynamic_capture.start()

print("CORREU TUDO BEM", flush=True)
background_thread2 = threading.Thread(target=schedule_backup, daemon=True)
background_thread2.start()

background_thread = threading.Thread(target=run_sysdig, daemon=True)
background_thread.start()





#main_threads["networks"] = background_thread2

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)