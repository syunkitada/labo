#!/bin/bash -xe

COMMAND="${@:-help}"

FRRVER="frr-stable"

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/networks/frr1"}'`
cd $ROOT

function init-node() {
    name=$1
    sudo docker ps | grep " ${name}$" && sudo docker kill ${name} || echo "${name} not found"
    sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name} || echo "${name} not found"
    sudo docker run --name ${name} -d \
        -it --privileged --rm --network none -v $ROOT/etc:/docker/etc --name $name centos7-frr-node:latest sh

    test -e /var/run/netns/$name && rm /var/run/netns/$name || echo "removed ns $name"
    PID=`sudo docker inspect --format '{{.State.Pid}}' $name`
    sudo ln -sfT /proc/$PID/ns/net /var/run/netns/$name

    sudo ip netns exec $name sysctl -w net.ipv4.ip_forward=1
    sudo ip netns exec $name sysctl -w net.ipv6.conf.all.disable_ipv6=0
    sudo ip netns exec $name sysctl -w net.ipv6.conf.default.disable_ipv6=0
}

function init-interface() {
    name=$1
    ip=$2
    sudo ip netns exec $name ip link add l3admin type dummy
    sudo ip netns exec $name ip addr add $ip/32 dev l3admin
    sudo ip netns exec $name ip link set l3admin up
}

function init-frr() {
    name=$1
    sudo docker exec $name ln -sf /docker/etc/frr/daemons /etc/frr/daemons
    sudo docker exec $name ln -sf /docker/etc/frr/$name-frr.conf /etc/frr/frr.conf
    sudo docker exec $name /usr/lib/frr/frrinit.sh start
    sudo docker exec $name /usr/lib/frr/frrinit.sh reload
}

function link-node() {
    name1=$1-$2-1
    name2=$1-$2-2
    sudo ip link add $name1 type veth peer name $name2
    sudo ip link set $name1 netns $1 up
    sudo ip link set $name2 netns $2 up
}

function init() {
    sudo mkdir -p /var/run/netns
    init-node hv111
    init-node hv112
    init-node lf111
    init-node lf112

    init-node hv121
    init-node hv122
    init-node lf121
    init-node lf122

    init-node sp11
    init-node sp12

    # 配線
    link-node lf111 hv111
    link-node lf111 hv112
    link-node lf112 hv111
    link-node lf112 hv112

    link-node lf121 hv121
    link-node lf121 hv122
    link-node lf122 hv121
    link-node lf122 hv122

    link-node sp11 lf111
    link-node sp11 lf112
    link-node sp12 lf121
    link-node sp12 lf122

    # init interface
    init-interface hv111 10.1.10.111
    init-interface hv112 10.1.10.112
    init-interface hv121 10.1.10.121
    init-interface hv122 10.1.10.122
    init-interface lf111 10.1.20.11
    init-interface lf112 10.1.20.12
    init-interface lf121 10.1.20.21
    init-interface lf122 10.1.20.22
    init-interface sp11 10.1.30.11
    init-interface sp12 10.1.30.12

    # init frr
    # init-frr hv1
    # init-frr lf1
    # init-frr sp1
}


$COMMAND
