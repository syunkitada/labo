#!/bin/bash -xe

source envrc
source localnet_utilsrc

declare -A vmdata=(
	["name"]="centos7-1.example.com"
	["vcpus"]="4"
	["mem"]="4096"
	["disk"]="40G"
	["image"]="centos7_custom"
	["defaultGateway"]=192.168.200.1
	["resolver"]=192.168.200.1
)

declare -A port1=(
    ["bridge"]="vm-br"
	["name"]="com-0"
	["vmMac"]="02:17:bd:b7:9b:7e"
	["vmIp"]="192.168.200.2"
	["vmSubnet"]="192.168.200.1/24"
)

COMMAND="${@:-help}"

function help() {
    cat << EOS
# start vm
./*.sh start

# stop vm
./*.sh stop

# destroy vm
./*.sh destroy

# console vm
./*.sh console

# monitor vm
./*.sh monitor
EOS
}

function start() {
    prepareBridge port1
    # prepareNetns port1
    # prepareConfigdrive vmdata port1
    # startQemu vmdata port1
    # registerPdns vmdata port1
}

function stop() {
    stopQemu vmdata
}

function destroy() {
    destroyQemu vmdata
}

function console() {
    consoleQemu vmdata
}

function log() {
    logQemu vmdata
}

function monitor() {
    monitorQemu vmdata
}

$COMMAND
