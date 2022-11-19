#!/bin/bash -xe

source envrc
source utilsrc

declare -A vmdata=(
	["name"]="centos7.example.com"
	["vcpus"]="8"
	["mem"]="8192"
	["disk"]="40G"
	["image"]="centos7_custom"
	["defaultGateway"]=192.168.100.1
	["resolver"]=192.168.10.1
)

declare -A port1=(
	["name"]="com-0"
	["vmIp"]="192.168.100.2"
	["vmMac"]="02:17:bd:b7:9b:7e"
	["vmIpSubnet"]="192.168.100.2/24"
	["vmSubnet"]="192.168.100.0/24"
	["netnsIp"]="169.254.32.1"
	["netnsGateway"]="169.254.1.1"
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
    prepareNetns port1
    prepareConfigdrive vmdata port1
    startQemu vmdata port1
    registerPdns vmdata port1
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
