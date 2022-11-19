#!/bin/bash -e

sudo brctl addbr tier12-br
sudo ip link set tier12-br up

sudo ip link add tier12-br-veth0 type veth peer name tier120-veth
sudo brctl addif tier12-br tier12-br-veth0
sudo ip link set tier12-br-veth0 up

sudo ip link add tier12-br-veth1 type veth peer name tier121-veth
sudo brctl addif tier12-br tier12-br-veth1
sudo ip link set tier12-br-veth1 up

sudo ip link add tier12-br-veth2 type veth peer name tier122-veth
sudo brctl addif tier12-br tier12-br-veth2
sudo ip link set tier12-br-veth2 up


sudo ip link set tier120-veth netns tier12
sudo ip netns exec tier12 ip addr add dev tier120-veth 10.120.0.10/24
sudo ip netns exec tier12 ip link set tier120-veth up

sudo ip netns add tier121
sudo ip link set tier121-veth netns tier121
sudo ip netns exec tier121 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier121 ip addr add dev tier121-veth 10.120.0.11/24
sudo ip netns exec tier121 ip link set lo up
sudo ip netns exec tier121 ip link set tier121-veth up
sudo ip netns exec tier121 route add default gw 10.120.0.1

sudo ip netns add tier122
sudo ip link set tier122-veth netns tier122
sudo ip netns exec tier122 sysctl net.ipv4.ip_forward=1
sudo ip netns exec tier122 ip addr add dev tier122-veth 10.120.0.12/24
sudo ip netns exec tier122 ip link set lo up
sudo ip netns exec tier122 ip link set tier122-veth up
sudo ip netns exec tier122 route add default gw 10.120.0.1
