#!/bin/bash -e

sudo brctl addbr tier11-br
sudo ip link set tier11-br up

sudo ip link add tier11-br-veth0 type veth peer name tier110-veth
sudo brctl addif tier11-br tier11-br-veth0
sudo ip link set tier11-br-veth0 up

sudo ip link add tier11-br-veth1 type veth peer name tier111-veth
sudo brctl addif tier11-br tier11-br-veth1
sudo ip link set tier11-br-veth1 up

sudo ip link add tier11-br-veth2 type veth peer name tier112-veth
sudo brctl addif tier11-br tier11-br-veth2
sudo ip link set tier11-br-veth2 up


sudo ip link set tier110-veth netns tier11
sudo ip netns exec tier11 ip addr add dev tier110-veth 10.110.0.10/24
sudo ip netns exec tier11 ip link set tier110-veth up

sudo ip netns add tier111
sudo ip link set tier111-veth netns tier111
sudo ip netns exec tier111 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier111 ip addr add dev tier111-veth 10.110.0.11/24
sudo ip netns exec tier111 ip link set lo up
sudo ip netns exec tier111 ip link set tier111-veth up
sudo ip netns exec tier111 route add default gw 10.110.0.1

sudo ip netns add tier112
sudo ip link set tier112-veth netns tier112
sudo ip netns exec tier112 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier112 ip addr add dev tier112-veth 10.110.0.12/24
sudo ip netns exec tier112 ip link set lo up
sudo ip netns exec tier112 ip link set tier112-veth up
sudo ip netns exec tier112 route add default gw 10.110.0.1
