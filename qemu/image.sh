#!/bin/bash

source envrc

COMMAND="${@:-help}"

function help() {
    cat << EOS
# show images
./image.sh list

# download centos7
./image.sh download-centos7

# download ubuntu20
./image.sh download-ubuntu20
EOS
}

CENTOS7_URL=https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2.xz

UBUNTU20_URL=https://cloud-images.ubuntu.com/releases/focal/release/ubuntu-20.04-server-cloudimg-amd64.img

function download() {
    IMAGE_TMP_PATH=${IMAGE_DIR}/$1.tmp
    IMAGE_PATH=${IMAGE_DIR}/$1
    IMAGE_URL=$2
    if [ ! -e $IMAGE_PATH ]; then
        if [ ! -e ${IMAGE_TMP_PATH} ]; then
            echo "downloading" $1 $2
            wget -O $IMAGE_TMP_PATH $IMAGE_URL
            echo "downloaded" $1 $2
        fi
        if file ${IMAGE_TMP_PATH} | grep 'XZ compressed data'; then
            cd ${IMAGE_DIR}
            mv ${IMAGE_TMP_PATH} ${IMAGE_TMP_PATH}.xz
            unxz ${IMAGE_TMP_PATH}.xz
            echo "compressed"
        fi
        if file ${IMAGE_TMP_PATH} | grep 'QEMU QCOW Image'; then
            mv ${IMAGE_TMP_PATH} ${IMAGE_PATH}
        else
            echo "Unexpected image type:" `file ${IMAGE_TMP_PATH}`
            exit 1
        fi
    else
        echo "already exists" $1 $2
    fi
    echo "success"
}

function download-centos7() {
    download $CENTOS7_IMG $CENTOS7_URL
}

function download-ubuntu20() {
    download $UBUNTU20_IMG $UBUNTU20_URL
}

function list() {
    ls -lh $IMAGE_DIR
}

$COMMAND
