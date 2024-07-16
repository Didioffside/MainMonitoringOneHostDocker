'''import requests
import yaml

def get_prometheus_targets(prometheus_url):
    targets_url = f"{prometheus_url}/api/v1/targets"

    response = requests.get(targets_url)

    if response.status_code == 200:
        targets_data = response.json()
        return targets_data['data']['activeTargets']
    else:
        print(f"Error: Unable to fetch targets. Status code: {response.status_code}")
        return None
    
prometheus_url = 'http://localhost:9090'
targets = get_prometheus_targets(prometheus_url)

if targets:
    print("List of Prometheus Targets:")
    print(type(targets))
    for target in targets:
        print(f" - {target['discoveredLabels']} ({target['labels']['instance']})")
        print(type(target))

file_path='./prometheus/prometheus.yml'
with open(file_path, 'r') as yaml_file:
    data = yaml.safe_load(yaml_file)
print(data, type(data), flush=True)
print("---------------------", flush=True)
print(data['scrape_configs'], flush=True)
print(len(data['scrape_configs']), flush=True)
print("1")
print(type(data['scrape_configs'][0]))
print("2")
for dic in data['scrape_configs']:
    print("3")
    print(dic['static_configs'])
    aux = dic['static_configs']
    print("4")
    for target in aux:
        print("5")
        print(target)
        print(type(target['targets'][0]))

all =[]
for j in data['scrape_configs']:
    aux = j['static_configs'][0]
    all.append(aux['targets'][0])

print(all)
print(type(all[0]))
dict = {}
for string in all:
    aux = string.split(':')
    aux_dict = {aux[0]: aux[1]}
    dict.update(aux_dict)
print(dict)

all=[]
dict = {}
cont=0
for j in data['scrape_configs']:
    aux = j['static_configs'][0]
    all.append(aux['targets'][0])
    aux1 = all[cont].split(':')
    cont+=1
    aux_dict = {aux1[0]: aux1[1]}
    dict.update(aux_dict)
print(dict)
'''
#{'global': {'scrape_interval': '15s'}, 'scrape_configs': [{'job_name': 'prometheus', 'static_configs': [{'targets': ['prometheus:9090']}]}, {'job_name': 'service1', 'static_configs': [{'targets': ['service1:5000']}]}, {'job_name': 'cadvisor', 'static_configs': [{'targets': ['cadvisor:8080']}]}]}


#NETWORK METRICS
'''import requests
from prometheus_api_client import PrometheusConnect
from datetime import datetime
import time


def query_prometheus(api_url, query):
    params = {'query': query}
    response = requests.get(f'{api_url}/api/v1/query', params=params)
    data = response.json()

    if response.status_code == 200:
        return data['data']['result']
    else:
        print(f'Error querying Prometheus: {data}')
        return None
    
prometheus_url = 'http://localhost:9090'
prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
metric_query = 'container_network_receive_packets_total'
metric_query2 = 'container_network_transmit_packets_total'
metric_query3 = 'container_network_receive_bytes_total'
metric_query4 = 'container_network_transmit_bytes_total'
metric_values = query_prometheus(prometheus_url, metric_query)

names_list = []
if metric_values:
    for result in metric_values:'''
        #print(result)
'''        metric_instance = result['metric']['instance']
        metric_value = float(result['value'][1])
        if 'name' in result['metric']:
            metric_name = result['metric']['name']
            names_list.append(metric_name)
            print(f'Metric Name: {metric_name}, Metric Instance: {metric_instance}, Metric_Value: {metric_value}')
        else:
            print(f'Metric Instance: {metric_instance}, Metric_Value: {metric_value}')


else:
    print('No metric values retrieved.')

print("TOU AQUII------------------------------")
for metric_name in names_list:
    print("METRIC NAME", metric_name)
    print("PACKET RATE")'''
    
    #rate_query = f'irate({metric_query}name='{metric_name}'}[1m])'
''' rate_query = "irate("+metric_query+"{name='"+metric_name+"'}[1m])"
    last_received_query = metric_query+"{name='"+metric_name+"'}"
    result = prom.custom_query(rate_query)'''
    #Packet Rate
''' print(result)

    result = prom.custom_query(query=last_received_query)
    print("LAST PACKET RECEIVED")'''
    #print(result)
    #print(result[0])
''' a = result[0]'''
    #print(result['value'])
''' b = a['value']'''
    #print(b)

''' timestamp = result[0]['value'][0]
    value = float(result[0]['value'][1])
    current_time = time.time()

    time_since_last_packet = current_time - timestamp

    print(f"Time since last packet was received is: {time_since_last_packet} seconds || Value: {value}")

    print("NUMBER OF PACKETS")'''

    #transmitted
''' result = prom.custom_query(query=metric_query2)
    
    a = result[0]
    b = a['value']
    value = float(b[1])
    print("Transmitted", value)

    result = prom.custom_query(query=metric_query)
    
    a = result[0]
    b = a['value']
    value = float(b[1])
    print("Received", value)

    print("BYTE RATE")
    
    rate_query = "irate("+metric_query3+"{name='"+metric_name+"'}[1m])"
    result = prom.custom_query(query=rate_query)
    print("Recevied", result)

    rate_query = "irate("+metric_query4+"{name='"+metric_name+"'}[1m])"
    result = prom.custom_query(query=rate_query)
    print("Transmit", result)'''
#auqi
#import docker
#import pyshark
#import time
#import subprocess
#import re
'''def capture_packets(container_id, network_interface, output_file):
    #capture = pyshark.LiveCapture(interface=network_interface, bpf_filter=f'container.id == {container_id}')
    capture = pyshark.LiveCapture(interface=network_interface)
    capture2 = capture.sniff(timeout=50)
    print(capture2, flush=True)'''

''' try:
        with open(output_file, 'w') as file:
            for packet in capture:
                # Extract packet type and delay information here
                packet_type = packet.layers[1].layer_name  # Assuming Ethernet layer is at index 1
                delay = time.time() - float(packet.sniff_timestamp)
                file.write(f"Packet Type: {packet_type}, Delay: {delay}\n")
                file.flush()
    except KeyboardInterrupt:
        print("Capture interrupted by user.")
    finally:
        capture.close()
'''



#----------------------------------------------------------------------------------------------------
#def capture_packets(container_id, network_name):
   #print(f"Capturing packets for container {container_id} on network {network_name}")
   #subprocess.run(["tcpdump", "-i", network_name, "-w", f"/tmp/capture_{container_id}.pcap"])
#--------------------------------------------------------------------------------------------------

#def find_interface_by_ip(ip_address):
 #   ip_a_output = subprocess.check_output(['ip', 'a']).decode('utf-8')
  #  print("OUTPUT-------", ip_a_output)
   # match = re.search(r'(?<=inet\s{})\s[^/]+'.format(re.escape(ip_address)), ip_a_output)
    #if match:
     #   return match.group().strip()
#def main():

 #   client = docker.from_env()
    #NEW ATTEMPT
    
    
  #  containers = client.containers.list()
 
   # for container in containers:
     #   container_id = container.id
    #    container_name = container.name
        #print(container_name)

      #  networks = container.attrs['NetworkSettings']['Networks']
       # print(networks)
        #for network_name, network_details in networks.items():
         #  if network_details.get('Gateway'):
          #     bridge_network_name = network_name
           #    ip_address = network_details.get('IPAddress', 'N/A')
            #   mac_address = network_details.get('MacAddress', 'N/A')

           #print(bridge_network_name, ip_address, mac_address)
           #print(find_interface_by_ip(ip_address))
           
           #if network_name != "bridge":
            #capture_packets(container_id, network_name)

    # Replace 'your_container_name_or_id' with the actual name or ID of the container you want to monitor
    #container_id = client.containers.get('ui').id

    # Replace 'br-2ee004f2d163' with the correct network interface associated with 'config_network'
    #network_interface = 'br-2ee004f2d163'

    #output_file = 'captured_packets.txt'

    #capture_packets(container_id, network_interface, output_file)
'''interface = 'br-3f04f8b117c1'
    capture = pyshark.LiveCapture(interface=interface)
    print("antes")
    capture.sniff(timeout=50)
    print(type(capture))
    print(capture)
    print("oi")
    aux = 0
    for packet in capture:
        if aux >= 20:
            break
        aux+=1
        print("what", flush=True)
        print(packet,flush=True)'''






#-------------------------------------------------------------------------------------------
############################################################################################
#testes.py
'''import re
import subprocess
import pyshark
def starts_with_integer_and_colon(s):
    pattern = re.compile(r'^\d+:')
    return bool(pattern.match(s))

def separate_input(input_text):
    lines = input_text.split('\n')
    result = []
    list_indexes = []
    cont_aux = 0
    print(len(lines))
    for line in lines:
        print("LINE",line)
        result1 = starts_with_integer_and_colon(line)
        print("RESULT",result1)
        if result1==True:
            list_indexes.append(cont_aux)
            cont_aux+=1
        else:
            cont_aux+=1
    print(list_indexes)

    for i in range(len(list_indexes)):
        if i < len(list_indexes)-1:
            result.append(lines[list_indexes[i]:list_indexes[i+1]])
        else:
            result.append(lines[list_indexes[i]:])

    return result'''

#def find_interface_by_ip(ip_address):

    #ip_a_output = subprocess.check_output(['ip', 'a']).decode('utf-8')
    #print("OUTPUT-------", ip_a_output)
    #match = re.search(r'(?<=inet\s{})\s[^/]+'.format(re.escape(ip_address)), ip_a_output)
    #if match:
     #   return match.group().strip()

'''def extract_strings(list_of_lists):
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

def extract_ip_numbers(list_of_lists):
    list_of_thirds = []
    for list in list_of_lists:
        list_of_thirds.append(list[2].strip())
    return list_of_thirds

def get_ip(string_list):
    ip_addresses = []
    ip_regex = r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b'
    for string in string_list:
        matches = re.findall(ip_regex, string)
        ip_addresses.extend(matches)

    return ip_addresses'''

'''def remove_veth_strings(string_list):
    return [s for s in string_list if not s.startswith("veth")]'''
'''def main():'''
    ##ip_a_output = subprocess.check_output(['ip', 'a']).decode('utf-8')
    #print(ip_a_output)
    #a = find_interface_by_ip()
    ##output_list = separate_input(ip_a_output)
    ##result = extract_strings(output_list)
    ##result1 = extract_ip_numbers(output_list)
    ##result2 = get_ip(result1)
    ##print(remove_veth_strings(result))
    #print(result1)
    ##print(result2)
    #print(output_list)
    #for string in output_list:
     #  print("-------")
      # print(string)
       #print("--------")
'''    interface = 'br-79b87d52c59a'
    capture = pyshark.LiveCapture(interface=interface)
    print("antes")
    capture.sniff(timeout=50)
    print(type(capture))
    print(capture)
    print("oi")
    aux = 0
    for packet in capture:
        if aux >= 20:
            break
        aux+=1
        print("what", flush=True)
        print(packet,flush=True)'''
import requests
from prometheus_api_client import PrometheusConnect
from datetime import datetime
import time

def query_prometheus(api_url, query):
    params = {'query': query}
    response = requests.get(f'{api_url}/api/v1/query', params=params)
    data = response.json()

    if response.status_code == 200:
        return data['data']['result']
    else:
        print(f'Error querying Prometheus: {data}')
        return None
    
prometheus_url = 'http://localhost:9090'
prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
metric_query = 'container_network_receive_packets_total'
metric_query2 = 'container_network_transmit_packets_total'
metric_query3 = 'container_network_receive_bytes_total'
metric_query4 = 'container_network_transmit_bytes_total'
metric_values = query_prometheus(prometheus_url, metric_query)
names_list = []
interface_list = []
#print("MetricVAELUS",metric_values)
if metric_values:
    for result in metric_values:
        #print("RESULT",result)
        metric_instance = result['metric']['instance']
        metric_interface = result['metric']['interface']
        #print("INSDTANCE", metric_instance)
        metric_value = float(result['value'][1])
        #print("VALUE", metric_value)
        if 'name' in result['metric']:
            metric_name = result['metric']['name']
            names_list.append(metric_name)
            interface_list.append(metric_interface)
            print(f'Metric Name: {metric_name}, Metric Instance: {metric_instance}, Metric_Value: {metric_value}')
        else:
            print(f'Metric Instance: {metric_instance}, Metric_Value: {metric_value}')


else:
    print('No metric values retrieved.')

print(names_list)
print(interface_list)

for i in range(len(names_list)):
    #print("METRIC_NAME", names_list[i])
    rate_query_received = "irate("+metric_query+"{name='"+names_list[i]+"', interface='"+interface_list[i]+"'}[1m])"
    rate_query_transmitted = "irate("+metric_query2+"{name='"+names_list[i]+"', interface='"+interface_list[i]+"'}[1m])"
    #print(rate_query)
    result = prom.custom_query(rate_query_received)
    result1 = prom.custom_query(rate_query_transmitted)
    #print(result)
    if result != []:

        dic_result = result[0]
        value_result = dic_result['value']
        #print(result)
        #print(type(result), len(result))
        #print(value_result)
    if result1 != []:
        dic_result1 = result1[0]
        value_result1 = dic_result1['value']

    print("NAME: ", names_list[i], "INTERFACE: ", interface_list[i], "RECEIVED: ", value_result, "TRANSMITTED: ", value_result1)


def main():
    print("oi")
if __name__ == "__main__":
    main()