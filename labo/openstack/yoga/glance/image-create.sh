#!/bin/bash -xe

openstack image show cirros || ( 
	(
		test -e /tmp/cirros-0.4.0-x86_64-disk.img || wget http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img -P /tmp
	) && openstack image create \
		--file /tmp/cirros-0.4.0-x86_64-disk.img \
		--disk-format qcow2 --container-format bare \
		--public \
		cirros
)
