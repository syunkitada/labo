#!/bin/bash -xe

source /opt/openstack/envrc

image_list=$(openstack image list -f value -c Name)
if ! echo "$image_list" | grep -q cirros; then
	curl -Lo /tmp/cirros-0.5.1-x86_64-disk.img http://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img
	openstack image create --public --container-format bare --disk-format qcow2 --file /tmp/cirros-0.5.1-x86_64-disk.img cirros
fi

flavor_list=$(openstack flavor list -f value -c Name)
if ! echo "$flavor_list" | grep -q 1v-512M-1G; then
	openstack flavor create --id 1 --ram 512 --disk 1 --vcpus 1 1v-512M-1G
fi

network_list=$(openstack network list -f value -c Name)
if ! echo "$network_list" | grep -q private; then
	openstack network create --provider-network-type local local-net
	openstack subnet create --network local-net local-net \
		--subnet-range 192.168.0.0/24 --gateway 192.168.0.1 --allocation-pool start=192.168.0.2,end=192.168.0.254
fi
