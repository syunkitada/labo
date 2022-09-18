#!/bin/bash -ex

COMMAND="${@:-help}"

function help() {
    echo "
init
clean
"
}

function init() {
    # ブリッジ作成
    sudo ip link add fabric-br type bridge
    sudo ip link set fabric-br up
    sudo ip addr add dev fabric-br 10.10.10.1/24

    # テスト用hostのnetns及びvethを作ってつなげる
    sudo ip netns add fabric-host1
    sudo ip netns add fabric-host2

    sudo ip link add host1-br-veth1 type veth peer name host1-br-veth
    sudo ip link set dev host1-br-veth1 master fabric-br
    sudo ip link set host1-br-veth1 up
    sudo ip link set dev host1-br-veth netns fabric-host1
    sudo ip netns exec fabric-host1 ip addr add dev host1-br-veth 10.10.10.2/24
    sudo ip netns exec fabric-host1 ip link set lo up
    sudo ip netns exec fabric-host1 ip link set host1-br-veth up
    sudo ip netns exec fabric-host1 ip route add default via 10.10.10.1

    sudo ip link add host2-br-veth1 type veth peer name host2-br-veth
    sudo ip link set dev host2-br-veth1 master fabric-br
    sudo ip link set host2-br-veth1 up
    sudo ip link set dev host2-br-veth netns fabric-host2
    sudo ip netns exec fabric-host2 ip addr add dev host2-br-veth 10.10.10.3/24
    sudo ip netns exec fabric-host2 ip link set lo up
    sudo ip netns exec fabric-host2 ip link set host2-br-veth up
    sudo ip netns exec fabric-host2 ip route add default via 10.10.10.1

    # 確認
    ip link show master fabric-br
    sudo ip netns exec fabric-host1 ip addr show host1-br-veth
    sudo ip netns exec fabric-host2 ip addr show host2-br-veth
}

function clean() {
    ip link show type bridge fabric-br && sudo ip link del fabric-br || echo "fabric-br has already been deleted"
    ip netns show grep '^fabric-host1 ' && sudo ip netns del fabric-host1 || echo "fabric-host1 has already been deleted"
    ip netns show grep '^fabric-host2 ' && sudo ip netns del fabric-host2 || echo "fabric-host2 has already been deleted"
    ip link show type veth host1-br-veth1 && sudo ip kink del host1-br-veth1 || echo "host1-br-veth1 has already been deleted"
    ip link show type veth host2-br-veth1 && sudo ip kink del host2-br-veth1 || echo "host2-br-veth1 has already been deleted"
}

$COMMAND
