#!/bin/bash -xe

source /adminrc

openstack flavor show 1v-1M-0G || (
	openstack flavor create --vcpus 1 --ram 1 --disk 0 1v-1M-0G
)
