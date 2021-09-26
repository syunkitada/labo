#!/bin/bash -xe

COMMAND="${@:-help}"

FRRVER="frr-stable"

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/networks/frr1"}'`
cd $ROOT

function start() {
    curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el7.noarch.rpm
    sudo yum install -y ./$FRRVER*

    sudo yum install -y frr frr-pythontools

    cp $ROOT/etc/frr/* /etc/frr/
}

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

function init() {
    sudo mkdir -p /var/run/netns
    init-node hv1
    init-node leaf1
    init-node spine1

    # 配線
    sudo ip link add leaf1-hv1-1 type veth peer name leaf1-hv1-2
    sudo ip link add spine1-leaf1-1 type veth peer name spine1-leaf1-2
    sudo ip link add spine2-leaf1-1 type veth peer name spine2-leaf1-2

    sudo ip link set leaf1-hv1-1 netns leaf1 up
    sudo ip link set leaf1-hv1-2 netns hv1 up

    sudo ip link set spine1-leaf1-1 netns spine1 up
    sudo ip link set spine2-leaf1-1 netns spine2 up

    sudo ip link set spine1-leaf1-2 netns leaf1 up
    sudo ip link set spine2-leaf1-2 netns leaf1 up

    sudo ip netns exec hv1 ip link add l3admin type dummy
    sudo ip netns exec hv1 ip addr add 10.1.10.1/32 dev l3admin
    sudo ip netns exec hv1 ip link set l3admin up

    sudo ip netns exec leaf1 ip link add l3admin type dummy
    sudo ip netns exec leaf1 ip addr add 10.1.20.1/32 dev l3admin
    sudo ip netns exec leaf1 ip link set l3admin up

    sudo ip netns exec spine1 ip link add l3admin type dummy
    sudo ip netns exec spine1 ip addr add 10.1.30.1/32 dev l3admin
    sudo ip netns exec spine1 ip link set l3admin up

    # setup frr
    sudo docker exec hv1 ln -sf /docker/etc/frr/daemons /etc/frr/daemons
    sudo docker exec hv1 ln -sf /docker/etc/frr/hv1-frr.conf /etc/frr/frr.conf
    sudo docker exec hv1 /usr/lib/frr/frrinit.sh start
    sudo docker exec hv1 /usr/lib/frr/frrinit.sh reload

    sudo docker exec leaf1 ln -sf /docker/etc/frr/daemons /etc/frr/daemons
    sudo docker exec leaf1 ln -sf /docker/etc/frr/leaf1-frr.conf /etc/frr/frr.conf
    sudo docker exec leaf1 /usr/lib/frr/frrinit.sh start
    sudo docker exec leaf1 /usr/lib/frr/frrinit.sh reload

    sudo docker exec spine1 ln -sf /docker/etc/frr/daemons /etc/frr/daemons
    sudo docker exec spine1 ln -sf /docker/etc/frr/spine1-frr.conf /etc/frr/frr.conf
    sudo docker exec spine1 /usr/lib/frr/frrinit.sh start
    sudo docker exec spine1 /usr/lib/frr/frrinit.sh reload
}


$COMMAND
