#!/bin/bash -xe

source /adminrc

openstack network show localnet || (
	openstack network create \
		--provider-network-type local localnet
)

openstack subnet show localnet || (
	openstack subnet create \
		--subnet-range 192.168.0.0/24 --gateway 192.168.0.1 --allocation-pool start=192.168.0.2,end=192.168.0.254 \
		--network localnet localnet
)
