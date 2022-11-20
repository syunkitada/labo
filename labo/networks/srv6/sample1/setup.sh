#!/bin/bash

set -x

# create namespaces
for ns in h1 h2 r1 r2 r3 r4; do
	ip netns del $ns
	ip netns add $ns
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

# setup veth pair
link h1 r1
link r1 r2
link r2 r3
link r3 h2
link r2 r4

# assign ipv6 addr
ip netns exec h1 ip addr add fc00:a::1/64 dev h1_r1
ip netns exec r1 ip addr add fc00:b::1/64 dev r1_r2
ip netns exec r2 ip addr add fc00:c::1/64 dev r2_r3
ip netns exec r3 ip addr add fc00:d::1/64 dev r3_h2
ip netns exec r2 ip addr add fc00:e::1/64 dev r2_r4

ip netns exec r1 ip addr add fc00:a::2/64 dev r1_h1
ip netns exec r2 ip addr add fc00:b::2/64 dev r2_r1
ip netns exec r3 ip addr add fc00:c::2/64 dev r3_r2
ip netns exec h2 ip addr add fc00:d::2/64 dev h2_r3
ip netns exec r4 ip addr add fc00:e::2/64 dev r4_r2

# add route
ip netns exec h1 ip -6 route add fc00:d::/64 via fc00:a::2
ip netns exec h1 ip -6 route add fc00:e::/64 via fc00:a::2
ip netns exec r1 ip -6 route add fc00:d::/64 via fc00:b::2
ip netns exec r1 ip -6 route add fc00:e::/64 via fc00:b::2
ip netns exec r2 ip -6 route add fc00:d::/64 via fc00:c::2
ip netns exec r4 ip -6 route add fc00:d::/64 via fc00:e::1

ip netns exec h2 ip -6 route add fc00:a::/64 via fc00:d::1
ip netns exec r4 ip -6 route add fc00:a::/64 via fc00:e::1
ip netns exec r3 ip -6 route add fc00:a::/64 via fc00:c::1
ip netns exec r2 ip -6 route add fc00:a::/64 via fc00:b::1

# start tcpdump
rm -rf /tmp/srv6-demo.pcap
timeout 20 ip netns exec r2 tcpdump -i r2_r1 ip6 -w /tmp/srv6-demo.pcap &

# ping with default path from h1 to h2
sleep 3
ip netns exec h1 ping -6 -c 1 fc00:d::2

for mode in encap inline; do
	# add seg6 route
	ip netns exec r1 ip -6 route del fc00:d::/64
	ip netns exec r1 ip -6 route add fc00:d::/64 encap seg6 mode $mode \
		segs fc00:e::2 dev r1_r2
	ip netns exec r1 ip -6 route show

	# ping with SRv6 path from h1 to h2
	sleep 3
	ip netns exec h1 ping -6 -c 1 fc00:d::2
done

for job in $(jobs -p); do
	wait "$job"
done
