import os
import paramiko
import random
import time
import json
import threading
import sys
from datetime import datetime
from threading import Thread

infra_config = json.load(open("../../config/infra_config.json"))
deployment_output = json.load(open("../../dump/infra/deployment_output.json"))
all_device_list = deployment_output.keys()
private_networks_dict = infra_config["private_networks"]
public_networks_dict = infra_config["public_networks"]
vm_config = json.load(open("../../config/vm_config.json"))

networks = []

latency_dict = {}

for n in private_networks_dict.keys():
    networks.append(n)
    latency_dict[n] = private_networks_dict[n]["latency_ms"]

for n in public_networks_dict.keys():
    networks.append(n)
    latency_dict[n] = public_networks_dict[n]["latency_ms"]

print latency_dict

container_vm = vm_config["container_VM"]
container_vm_names = container_vm.keys()


pub_sub_data = "data"
path = "violet/sanity/pub_sub"


pub_list_txt = open('pub_sub_broker.txt', 'r')


print
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print "               Sanity check                   "
print "+++++++++++++++++++++++++++++++++++++++++++++++"
print

pub_list = pub_list_txt.readlines()

print len(pub_list)

pub_file_list = []
sub_file_list = []
lat_file_list = []

tmp_dir = "../../dump/sanity/pub_sub"

brokers = set()

for pl in pub_list:
    if len(pl.split()) != 6 :
	continue
    pub, sub, broker, topic, network, sensor_link = pl.split()
    brokers.add(broker)
    print "\nGetting pub sub and latency data from {0}".format(pub)
    if network == "private":
        network_name = deployment_output[pub]["private_networks"].keys()
        #print network_name[0]
    else:
        network_name = deployment_output[pub]["public_networks"].keys()
        #print network_name[0]

    vm_name = deployment_output[pub]["host_vm_name"]
    tmp_fog_dir = tmp_dir + "/" + network_name[0]
    tmp_fog_device_dir = tmp_fog_dir + "/" + pub
    host = container_vm[vm_name]["hostname_ip"]
    user = container_vm[vm_name]["user"]
    key = container_vm[vm_name]["key_path"]
    k = paramiko.RSAKey.from_private_key_file(key)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    c.connect(hostname = host, username = user, pkey = k)

    pub_file = "pub_" + topic
    sub_file = "sub_" + topic
    lat_file = "latency_" + topic

    pub_file_list.append(pub_file)
    sub_file_list.append(sub_file)
    lat_file_list.append(lat_file)

    commands = [
	"mkdir -p {0}".format(path),
        "sudo docker cp {0}:{1}/{2}/{3} {4}".format(pub,path,pub_sub_data,pub_file,path),
        "sudo docker cp {0}:{1}/{2}/{3} {4}".format(pub,path,pub_sub_data,sub_file,path),
        "sudo docker cp {0}:{1}/{2}/{3} {4}".format(pub,path,pub_sub_data,lat_file,path)
    ]

    for command in commands:
        #print command
        stdin, stdout, stderr = c.exec_command(command)
        if stderr.read() is not " ": print stderr.read()
    c.close()

    time.sleep(0.2)

    commands = [
            "mkdir -p {0}".format(tmp_fog_device_dir),
            "scp -i {0} {1}@{2}:{3}/{4} {5}".format(key, user, host, path, pub_file, tmp_fog_device_dir),
            "scp -i {0} {1}@{2}:{3}/{4} {5}".format(key, user, host, path, sub_file, tmp_fog_device_dir),
            "scp -i {0} {1}@{2}:{3}/{4} {5}".format(key, user, host, path, lat_file, tmp_fog_device_dir),
            "wc -l {0}".format(tmp_fog_device_dir + "/" + lat_file),
            "cat {0}/{1} >> {2}/{3}".format(tmp_fog_device_dir, lat_file, tmp_dir, network_name[0]+"_latency.txt")
            ]

    for command in commands:
        os.system(command)


print brokers

for b in list(brokers):
    vm_name = deployment_output[b]["host_vm_name"]
    tmp_fog_dir = tmp_dir + "/" + network_name[0]
    tmp_fog_device_dir = tmp_fog_dir + "/" + b
    pvt_log_file = "mosquitto-private.log"
    pub_log_file = "mosquitto-public.log"
    host = container_vm[vm_name]["hostname_ip"]
    user = container_vm[vm_name]["user"]
    key = container_vm[vm_name]["key_path"]
    k = paramiko.RSAKey.from_private_key_file(key)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    c.connect(hostname = host, username = user, pkey = k)
    
    commands = [
            "mkdir -p {0}".format(tmp_fog_device_dir)
    ]

    for command in commands:
	os.system(command)

    commands = [
            #"scp -i {0} {1}@{2}:{3}/{4} {5}".format(key, user, host, path, pub_file, tmp_fog_device_dir),
            #"scp -i {0} {1}@{2}:{3}/{4} {5}".format(key, user, host, path, sub_file, tmp_fog_device_dir),
            #"scp -i {0} {1}@{2}:{3}/{4} {5}".format(key, user, host, path, lat_file, tmp_fog_device_dir),
            #"wc -l {0}".format(tmp_fog_device_dir + "/" + lat_file),
	    "mkdir -p {0}/{1}".format(path,b),
	    "sudo docker cp {0}:{1}/{2} {3}/{0}".format(b,path,pub_log_file,path),
	    "sudo docker cp {0}:{1}/{2} {3}/{0}".format(b,path,pvt_log_file,path)
            #"sudo docker exec -it {0} bash -c 'cat {3}/{2} > {1}/{2}'".format(b, tmp_fog_device_dir, pub_log_file, "/violet/sanity/pub_sub"),
	    #"sudo docker exec -it {0} bash -c 'cat {3}/{2} > {1}/{2}'".format(b, tmp_fog_device_dir, pvt_log_file, "/violet/sanity/pub_sub")
            ]

    for command in commands:
	print command
        stdin, stdout, stderr = c.exec_command(command)
	print stderr.read()
    c.close()

    commands = [
	"mkdir -p {0}".format(tmp_fog_device_dir),
        "scp -i {0} {1}@{2}:{3}/{4}/{5} {6}".format(key, user, host, path, b, pub_log_file, tmp_fog_device_dir),
        "scp -i {0} {1}@{2}:{3}/{4}/{5} {6}".format(key, user, host, path, b, pvt_log_file, tmp_fog_device_dir)
    ]

    for command in commands:
        os.system(command)



networks.sort()

for network in networks:
    f = open(tmp_dir + "/" + network + "_latency.txt", "r")
    expected = float(latency_dict[network]) * 4
    latencies = f.readlines()
    f.close()
    d = open(tmp_dir + "/" + network + "_deviation.txt", "w")
    for lat in latencies:
        dev = (((float(lat) * 1000) - expected) / expected) * 100
        d.write(str(dev) + "\n")

    d.close()



print "\n\nGenerating Plot\n\n"
plot_in_file = tmp_dir + "/latency_deviation.txt"

command = "paste -d ',' "

for network in networks:
    #print network
    command += tmp_dir + "/" + network + "_deviation.txt" + " "

command += " > {0}".format(plot_in_file)

os.system(command)

plot_out_file = tmp_dir + "/latency_deviation"

command = 'python ../../dump/sanity/vPlot.py {0} {1} "'.format(plot_in_file, plot_out_file)

for network in networks:
    #print network
    command += network + ","

#command = command[:len(command) - 1]

command += '" "Latency Deviation % " "Networks"'

os.system(command)

