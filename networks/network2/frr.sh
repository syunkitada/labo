#!/bin/bash -xe

COMMAND="${@:-help}"

FRRVER="frr-stable"

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/networks/network2"}'`
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
        -it --privileged --rm --network none -v $ROOT/etc:/docker/etc --name $name centos7-node:latest sh

    test -e /var/run/netns/$name && rm /var/run/netns/$name || echo "removed ns $name"
    PID=`sudo docker inspect --format '{{.State.Pid}}' $name`
    sudo ln -sfT /proc/$PID/ns/net /var/run/netns/$name

    sudo ip netns exec $name sysctl -w net.ipv6.conf.all.disable_ipv6=0
    sudo ip netns exec $name sysctl -w net.ipv6.conf.default.disable_ipv6=0
}

function init() {
    sudo mkdir -p /var/run/netns
    init-node leaf1
    init-node leaf2
    init-node spine1
    init-node spine2

    sudo ip link add spine1-leaf1-1 type veth peer name spine1-leaf1-2
    sudo ip link add spine2-leaf1-1 type veth peer name spine2-leaf1-2

    sudo ip link set spine1-leaf1-1 netns spine1 up
    sudo ip link set spine2-leaf1-1 netns spine2 up

    sudo ip link set spine1-leaf1-2 netns leaf1 up
    sudo ip link set spine2-leaf1-2 netns leaf1 up

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
