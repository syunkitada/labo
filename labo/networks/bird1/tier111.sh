#!/bin/bash -e

sudo brctl addbr tier111-br
sudo ip link set tier111-br up

sudo ip link add tier111br-veth0 type veth peer name as1110-veth
sudo brctl addif tier111-br tier111br-veth0
sudo ip link set tier111br-veth0 up

sudo ip link add tier111br-veth1 type veth peer name as1111-veth
sudo brctl addif tier111-br tier111br-veth1
sudo ip link set tier111br-veth1 up

sudo ip link add tier111br-veth2 type veth peer name as1112-veth
sudo brctl addif tier111-br tier111br-veth2
sudo ip link set tier111br-veth2 up

# as111
sudo ip link set as1110-veth netns tier111
sudo ip netns exec tier111 ip addr add dev as1110-veth 10.111.0.10/24
sudo ip netns exec tier111 ip link set as1110-veth up

# as1111
sudo ip netns add as1111
sudo ip link set as1111-veth netns as1111
sudo ip netns exec as1111 sysctl net.ipv4.ip_forward=1
sudo ip netns exec as1111 ip addr add dev as1111-veth 10.111.0.11/24
sudo ip netns exec as1111 ip link set lo up
sudo ip netns exec as1111 ip link set as1111-veth up
sudo ip netns exec as1111 route add default gw 10.111.0.1

# as1112
sudo ip netns add as1112
sudo ip link set as1112-veth netns as1112
sudo ip netns exec as1112 sysctl net.ipv4.ip_forward=1
sudo ip netns exec as1112 ip addr add dev as1112-veth 10.111.0.12/24
sudo ip netns exec as1112 ip link set lo up
sudo ip netns exec as1112 ip link set as1112-veth up
sudo ip netns exec as1112 route add default gw 10.111.0.1
