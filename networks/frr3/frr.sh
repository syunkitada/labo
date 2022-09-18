#!/bin/bash -xe

COMMAND="${@:-help}"

FRRVER="frr-stable"

ROOT=`echo $PWD | awk -F setup-scripts '{print $1"setup-scripts/networks/frr3"}'`
cd $ROOT

function init-node() {
    name=$1
    sudo docker ps | grep " ${name}$" && sudo docker kill ${name} || echo "${name} not found"
    sudo docker ps --all | grep " ${name}$" && sudo docker rm ${name} || echo "${name} not found"
    sudo docker run --name ${name} -d \
        -it --privileged --rm --network none -v /tmp/docker:/docker/tmp -v $ROOT/etc:/docker/etc --name $name centos7-frr-node:latest sh

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
    as=$2
    ip=$3
    interfaces=$4

    sudo docker exec $name ln -sf /docker/etc/frr/daemons /etc/frr/daemons

    interfacesConf=""
    bgpNeighborsConf=""
    for interface in $interfaces
    do
        interfacesConf+="
interface ${interface}
  ipv6 nd ra-interval 10
  no ipv6 nd suppress-ra
!
"
        bgpNeighborsConf+="neighbor ${interface} interface peer-group ADMIN
  "
    done

    cat << EOS | sudo tee /tmp/docker/$name-frr.conf
frr defaults datacenter
hostname hv1

log file /var/log/frr/frr.log
!

${interfacesConf}

router bgp ${as}
  bgp router-id ${ip}
  bgp bestpath as-path multipath-relax

  neighbor ADMIN peer-group
  neighbor ADMIN remote-as external
  neighbor ADMIN capability extended-nexthop

  ${bgpNeighborsConf}

  address-family ipv4 unicast
    network ${ip}/32
  exit-address-family
!

line vty
!
EOS

    sudo docker exec $name ln -sf /docker/tmp/$name-frr.conf /etc/frr/frr.conf
    sudo docker exec $name /usr/lib/frr/frrinit.sh restart
    sudo docker exec $name /usr/lib/frr/frrinit.sh reload
}

function add-vm-route() {
    name=$1
    as=$2
    network=$3
    sudo docker exec $name vtysh -c "configure terminal" \
        -c "router bgp ${as}" \
        -c "address-family ipv4 unicast" \
        -c "network ${network}" \
        -c "exit-address-family" \
        -c "exit"
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
    link-node sp11 lf121
    link-node sp11 lf122
    link-node sp12 lf111
    link-node sp12 lf112
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
    init-frrs
}

function init-frrs() {
    init-frr hv111 4200110111 10.1.10.111 "lf111-hv111-2 lf112-hv111-2"
    init-frr hv112 4200110112 10.1.10.112 "lf111-hv112-2 lf112-hv112-2"
    init-frr hv121 4200110121 10.1.10.121 "lf121-hv121-2 lf122-hv121-2"
    init-frr hv122 4200110122 10.1.10.122 "lf121-hv122-2 lf122-hv122-2"
    init-frr lf111 4200120111 10.1.20.11  "lf111-hv111-1 lf111-hv112-1 sp11-lf111-2 sp12-lf111-2"
    init-frr lf112 4200120112 10.1.20.12  "lf112-hv111-1 lf112-hv112-1 sp11-lf112-2 sp12-lf112-2"
    init-frr lf121 4200120111 10.1.20.21  "lf121-hv121-1 lf121-hv122-1 sp11-lf121-2 sp12-lf121-2"
    init-frr lf122 4200120112 10.1.20.22  "lf122-hv121-1 lf122-hv122-1 sp11-lf122-2 sp12-lf122-2"
    init-frr sp11  4200130011 10.1.30.11  "sp11-lf111-1 sp11-lf112-1 sp11-lf121-1 sp11-lf122-1"
    init-frr sp12  4200130012 10.1.30.12  "sp12-lf111-1 sp12-lf112-1 sp12-lf121-1 sp12-lf122-1"
}


$COMMAND
