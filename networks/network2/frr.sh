#!/bin/bash -e

COMMAND="${@:-help}"

FRRVER="frr-stable"

function start() {
    curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el7.noarch.rpm
    sudo yum install -y ./$FRRVER*

    sudo yum install -y frr frr-pythontools
}

$COMMAND
