#!/bin/bash -e

sudo brctl addbr as1111-16-br
sudo ip link set as1111-16-br up

sudo ip link add as111116-veth0 type veth peer name as111116-veth00
sudo brctl addif as1111-16-br as111116-veth0
sudo ip link set as111116-veth0 up

sudo ip link add as111116-veth1 type veth peer name as111116-veth11
sudo brctl addif as1111-16-br as111116-veth1
sudo ip link set as111116-veth1 up


sudo ip link set as111116-veth00 netns as1111
sudo ip netns exec as1111 ip addr add dev as111116-veth00 10.111.1.17/28
sudo ip netns exec as1111 ip link set as111116-veth00 up

sudo ip netns add as1111-16-server1
sudo ip link set as111116-veth11 netns as1111-16-server1
sudo ip netns exec as1111-16-server1 ip addr add dev as111116-veth11 10.111.1.21/28
sudo ip netns exec as1111-16-server1 ip link set lo up
sudo ip netns exec as1111-16-server1 ip link set as111116-veth11 up
sudo ip netns exec as1111-16-server1 route add default gw 10.111.1.17
