#!/bin/bash

set -x

# create namespaces
for ns in r1 h1 h2; do
	ip netns del $ns
	ip netns add $ns
	ip netns exec $ns ip link set lo up
	ip netns exec $ns sysctl net.ipv4.conf.all.rp_filter=0
	ip netns exec $ns sysctl net.ipv4.conf.default.rp_filter=0
	ip netns exec $ns sysctl net.ipv4.conf.all.forwarding=1
	ip netns exec $ns sysctl net.ipv4.conf.default.forwarding=1
	ip netns exec $ns sysctl net.ipv6.conf.all.forwarding=1
	ip netns exec $ns sysctl net.ipv6.conf.default.forwarding=1
	ip netns exec $ns sysctl net.ipv6.conf.all.seg6_enabled=1
	ip netns exec $ns sysctl net.ipv6.conf.default.seg6_enabled=1
done

# setup veth pair
function link() {
	ip link add "$1_$2" type veth peer name "$2_$1"
	ip link set "$1_$2" netns "$1"
	ip link set "$2_$1" netns "$2"
	ip netns exec "$1" ip link set "$1_$2" up
	ip netns exec "$2" ip link set "$2_$1" up
}

link r1 h1
link r1 h2

# assign ipv6 addr
ip netns exec h1 ip addr add fc00:a::2/64 dev h1_r1
ip netns exec r1 ip addr add fc00:a::1/64 dev r1_h1

ip netns exec r1 ip addr add fc00:b::1/64 dev r1_h2
ip netns exec h2 ip addr add fc00:b::2/64 dev h2_r1

# add route
ip netns exec h1 ip -6 route add fc00:b::/64 via fc00:a::1
ip netns exec h2 ip -6 route add fc00:a::/64 via fc00:b::1

# setup for srv6
ip netns exec h1 ip addr add 10.10.10.2/24 dev lo
ip netns exec h1 ip sr tunsrc set fc00:a::2
ip netns exec h1 ip route add 10.10.10.3 encap seg6 mode encap segs fc00:b::2 dev h1_r1
ip netns exec h1 ip -6 route add fc00:a::2/128 encap seg6local action End.DX4 nh4 10.10.10.2 dev h1_r1

ip netns exec h2 ip addr add 10.10.10.3/24 dev lo
ip netns exec h2 ip sr tunsrc set fc00:b::2
ip netns exec h2 ip route add 10.10.10.2 encap seg6 mode encap segs fc00:a::2 dev h2_r1
ip netns exec h2 ip -6 route add fc00:b::2/128 encap seg6local action End.DX4 nh4 10.10.10.3 dev h2_r1

sleep 3
ip netns exec h1 ping -6 -c 1 fc00:b::2
ip netns exec h1 ping -c 1 10.10.10.3
