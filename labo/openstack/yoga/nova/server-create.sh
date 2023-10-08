#!/bin/bash -xe

openstack server create --flavor 1v-1M-0G --network localnet --image cirros testvm1
