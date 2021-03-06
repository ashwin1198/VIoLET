import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from pylab import *
import json
import sys

metis_partitions = json.load(open("metis_partitions.json","r"))
device_types = json.load(open("../../config/device_types.json","r"))
vm_types = json.load(open("../../config/vm_types.json","r"))
infra_config = json.load(open("../../config/infra_config.json","r"))
devices = infra_config["devices"]


networks = []

nw_coremark = {}
nw_memory = {}
nw_disk = {}
nw_devices = {}


vm_config = json.load(open("../../config/vm_config.json"))
vm_names = vm_config["container_VM"].keys()

vm_coremark = vm_types[vm_config["container_VM"][vm_names[0]]["vm_type"]]["coremark"]

print
print vm_names
print

metis_data = []
metis_devices = []

for vm in vm_names:
	nw_coremark[vm] = {}
        nw_memory[vm] = {}
        nw_disk[vm] = {}
	nw_devices[vm] = {}

for device in metis_partitions:
	vm = vm_names[int(metis_partitions[device])]

	nw_coremark[vm][device] = int(device_types[devices[device]["device_type"]]["coremark"])/1000
        nw_memory[vm][device] = int(device_types[devices[device]["device_type"]]["memory_mb"])/1000
        nw_disk[vm][device] = int(device_types[devices[device]["device_type"]]["disk_mb"])/1000
	nw_devices[vm][device] = device

metis_devices.append(nw_devices)

if sys.argv[1] == "coremark":
	metis_data.append(nw_coremark)
elif sys.argv[1] == "memory":
	metis_data.append(nw_memory)
elif sys.argv[1] == "disk":
	metis_data.append(nw_disk)
else:
	print "Incorrect input"
	sys.exit(0)

print "metis devices"
print metis_devices

metis_order = []
dataset = []
deviceset = []
colors = {'Pi2B':'#00a8ff','Pi3B':'#c64847','Pi3B+':'#f195ac','TX1':'#b28bc0','SI':'#7fd13b'}
labels = {'#00a8ff':'Pi2B','#c64847':'Pi3B','#f195ac':'Pi3B+','#b28bc0':'TX1','#7fd13b':'SI'}
metis_colors = []

for i in range(len(metis_data)):
	for vm in vm_names:
		dataset.append(metis_data[i][vm])
		deviceset.append(metis_devices[i][vm])
		order = []
		col = []
		for d in metis_data[i][vm].keys():
			order.append(d)
			col.append(colors[devices[d]["device_type"]])
		metis_order.append(order)
		metis_colors.append(col)



max_length = max(len(d) for d in dataset)
print max_length
i = 0
for d in dataset:
	l = max_length - len(d)
	while l>0:
		d[devices.keys()[l]] = 0
		metis_order[i].append(devices.keys()[l])
		#metis_devices[i].append(devices.keys()[l])
		l-=1
	i+=1

i=0
for d in deviceset:
	l = max_length - len(d)
	while l>0:
		d[devices.keys()[l]] = ' '
		l-=1
	i+=1
	
print "dataset"	
print dataset
#print metis_colors
data_orders = metis_order
print data_orders
print "deviceset"
print deviceset

#for i in range(len(data_orders)):
#	data_orders[i] = sorted(data_orders[i])
	

#print "sorted"
#print metis_order


values = np.array([[data[name] for name in order] for data,order in zip(dataset, data_orders)])
print values
devices = np.array([[dev[name] for name in order] for dev,order in zip(deviceset, data_orders)])
print devices
lefts=np.insert(np.cumsum(values,axis=1),0,0,axis=1)[:,:-1]
print lefts
orders = np.array(data_orders)
print orders
bottoms = np.arange(len(data_orders))
print bottoms
#fig = plt.figure(1,figsize=(9, 6))
fig,ax = plt.subplots()


index = 0
for names,color in zip(dataset,metis_colors):
	print "names,coloe,devices"
	print names,color,devices
	idx = np.where(orders==names.keys())
	value = values[idx]
	print value
	left = lefts[idx]
	print left
	device = devices[idx]
	#index=0
	k=0
	for n,c,v,l in zip(names,color,value,left):
		boxes = plt.bar(left=bottoms[index],height=v,width=0.3,bottom=l,color=c,edgecolor='black',orientation='vertical')
		text(bottoms[index],l,device[k],size=15)
		k+=1
	index+=1
#index%=3


plt.xticks(bottoms, vm_names,size=25)
plt.yticks(size=25)
ax.set_title("{}".format(sys.argv[1]),size=25)
ax.set_xlabel("Virtual Machines",size=25)

if sys.argv[1] == "coremark":
	ax.set_ylabel("{} (K)".format(sys.argv[1]),size=25)
elif sys.argv[1] == "memory":
	ax.set_ylabel("{} (GB)".format(sys.argv[1]),size=25)
elif sys.argv[1] == "disk":
	ax.set_ylabel("{} (GB)".format(sys.argv[1]),size=25)


plt.legend(loc="best", bbox_to_anchor=(1.0, 1.00))
plt.subplots_adjust(right=0.85)

plt.show()

fig = matplotlib.pyplot.gcf()
fig.set_size_inches(8, 6)

######################################################################
###########            Plot Computation Ends          ################
######################################################################

# Save the figure
fig.savefig(sys.argv[1]+".png", bbox_inches='tight')
print("\n[SUCCESS] : Plot generated Successfully!")
print("[PATH] : " + sys.argv[1]+".png")

