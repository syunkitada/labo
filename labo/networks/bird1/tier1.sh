#!/bin/bash -e

sudo brctl addbr tier1-br
sudo ip link set tier1-br up

sudo ip link add tier1-br-veth1 type veth peer name tier11-veth
sudo brctl addif tier1-br tier1-br-veth1
sudo ip link set tier1-br-veth1 up

sudo ip link add tier1-br-veth2 type veth peer name tier12-veth
sudo brctl addif tier1-br tier1-br-veth2
sudo ip link set tier1-br-veth2 up

sudo ip link add tier1-br-veth3 type veth peer name tier13-veth
sudo brctl addif tier1-br tier1-br-veth3
sudo ip link set tier1-br-veth3 up


sudo ip netns add tier11
sudo ip link set tier11-veth netns tier11
sudo ip netns exec tier11 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier11 ip addr add dev tier11-veth 10.1.0.11/24
sudo ip netns exec tier11 ip link set lo up
sudo ip netns exec tier11 ip link set tier11-veth up
sudo ip netns exec tier11 route add default gw 10.1.0.1

sudo ip netns add tier12
sudo ip link set tier12-veth netns tier12
sudo ip netns exec tier12 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier12 ip addr add dev tier12-veth 10.1.0.12/24
sudo ip netns exec tier12 ip link set lo up
sudo ip netns exec tier12 ip link set tier12-veth up
sudo ip netns exec tier12 route add default gw 10.1.0.1

sudo ip netns add tier13
sudo ip link set tier13-veth netns tier13
sudo ip netns exec tier13 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier13 ip addr add dev tier13-veth 10.1.0.13/24
sudo ip netns exec tier13 ip link set lo up
sudo ip netns exec tier13 ip link set tier13-veth up
sudo ip netns exec tier13 route add default gw 10.1.0.1


sudo mkdir -p /etc/bird/
