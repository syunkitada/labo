#!/bin/bash -xe

source /adminrc

openstack server show testvm1 || (
	openstack server create --flavor 1v-1M-0G --network localnet --image cirros testvm1
)

timeout 5 bash -c "until openstack server show testvm1 | grep ACTIVE; do sleep 1; done"
