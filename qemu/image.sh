#!/bin/bash

source envrc
source utilsrc

COMMAND="${@:-help}"

function help() {
    cat << EOS
list
delete [image name]
download-centos7
download-rocky8
download-ubuntu20
umount-qemu-nbd [image name]
mount-qemu-nbd [image name]
custom-img [image name]
EOS
}

MOUNT_PATH=/mnt/qemu-nbd

CENTOS7_URL=https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2.xz

ROCKY8_URL=https://download.rockylinux.org/pub/rocky/8.4/images/Rocky-8-GenericCloud-8.4-20210620.0.x86_64.qcow2

UBUNTU20_URL=https://cloud-images.ubuntu.com/releases/focal/release/ubuntu-20.04-server-cloudimg-amd64.img


function _download() {
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
    _download $CENTOS7_IMG $CENTOS7_URL
}

function download-rocky8() {
    _download $ROCKY8_IMG $ROCKY8_URL
}

function download-ubuntu20() {
    _download $UBUNTU20_IMG $UBUNTU20_URL
}

function list() {
    ls -lh $IMAGE_DIR
}

function delete() {
    if [ $# != 1 ]; then
        help
        exit 1
    fi
    rm $IMAGE_DIR/$1
}

function umount-qemu-nbd() {
    mount | grep $MOUNT_PATH && sudo umount $MOUNT_PATH || echo "already unmounted"
    sudo qemu-nbd --disconnect /dev/nbd0
    sudo rm -rf $MOUNT_PATH
}

# MEMO: qemu-nbdにより、nbd(network block device)経由で、qcow2などの仮想ディスクイメージを物理デバイスのように扱うことができる
function mount-qemu-nbd() {
    if [ $# != 1 ]; then
        help
        exit 1
    fi
    umount-qemu-nbd

    path=$IMAGE_DIR/$1
    test -e $path || (echo "file is not found: $path" && exit 1)

    sudo modprobe nbd max_part=63
    sudo mkdir -p $MOUNT_PATH
    until sudo qemu-nbd -c /dev/nbd0 $path; do
        sleep 1
    done
    until sudo mount /dev/nbd0p1 $MOUNT_PATH; do
        sleep 1
    done
}

function _init-centos7-img() {
    sudo mount -o bind /dev /mnt/qemu-nbd/dev
    sudo cp myinit/myinit.service /mnt/qemu-nbd/etc/systemd/system/
    sudo mkdir -p /mnt/qemu-nbd/opt/myinit/bin
    sudo cp myinit/myinit /mnt/qemu-nbd/opt/myinit/bin/myinit
    sudo chroot /mnt/qemu-nbd systemctl enable myinit.service

    sudo chroot /mnt/qemu-nbd yum remove -y cloud-init

    sudo chroot /mnt/qemu-nbd yum install -y dnsmasq

    # admin userの作成
    grep '^admin:' /mnt/qemu-nbd/etc/group || sudo chroot /mnt/qemu-nbd groupadd admin
    sudo chroot /mnt/qemu-nbd useradd -g admin admin
    echo 'admin:admin' | sudo chroot /mnt/qemu-nbd chpasswd
    sudo mkdir -p /mnt/qemu-nbd/home/admin
    sudo grep "%admin ALL=(ALL) ALL" /mnt/qemu-nbd/etc/sudoers || sudo sed -i '$ i %admin ALL=(ALL) ALL' /mnt/qemu-nbd/etc/sudoers

    # disable selinux
    sudo sed -i  's/^SELINUX=.*/SELINUX=disabled/g' /mnt/qemu-nbd/etc/selinux/config

    # 80-net-setup-link.rules があると、udevによって自動でifcfg-eth0を生成してしまうため削除する
    # デフォルトだとdhcpが利用されてしまうため、dhcpがタイムアウトで失敗するまで待たされてしまう
    sudo rm -rf /mnt/qemu-nbd/lib/udev/rules.d/80-net-setup-link.rules
    # network-scripts/ifcfg-eth0(anacondaで作成された?)が残ってるので削除してく
    sudo rm -rf /mnt/qemu-nbd/etc/sysconfig/network-scripts/ifcfg-eth0

    sudo umount /mnt/qemu-nbd/dev
}

function _init-rocky8-img() {
    sudo mount -o bind /dev /mnt/qemu-nbd/dev
    sudo cp myinit/myinit.service /mnt/qemu-nbd/etc/systemd/system/
    sudo mkdir -p /mnt/qemu-nbd/opt/myinit/bin
    sudo cp myinit/myinit /mnt/qemu-nbd/opt/myinit/bin/myinit
    sudo chroot /mnt/qemu-nbd systemctl enable myinit.service

    sudo chroot /mnt/qemu-nbd yum remove -y cloud-init

    sudo chroot /mnt/qemu-nbd yum install -y dnsmasq

    # admin userの作成
    grep '^admin:' /mnt/qemu-nbd/etc/group || sudo chroot /mnt/qemu-nbd groupadd admin
    sudo chroot /mnt/qemu-nbd useradd -g admin admin
    echo 'admin:admin' | sudo chroot /mnt/qemu-nbd chpasswd
    sudo mkdir -p /mnt/qemu-nbd/home/admin
    sudo grep "%admin ALL=(ALL) ALL" /mnt/qemu-nbd/etc/sudoers || sudo sed -i '$ i %admin ALL=(ALL) ALL' /mnt/qemu-nbd/etc/sudoers

    # disable selinux
    sudo sed -i  's/^SELINUX=.*/SELINUX=disabled/g' /mnt/qemu-nbd/etc/selinux/config

    # 80-net-setup-link.rules があると、udevによって自動でifcfg-eth0を生成してしまうため削除する
    # デフォルトだとdhcpが利用されてしまうため、dhcpがタイムアウトで失敗するまで待たされてしまう
    sudo rm -rf /mnt/qemu-nbd/lib/udev/rules.d/80-net-setup-link.rules
    # network-scripts/ifcfg-eth0(anacondaで作成された?)が残ってるので削除してく
    sudo rm -rf /mnt/qemu-nbd/etc/sysconfig/network-scripts/ifcfg-eth0

    sudo umount /mnt/qemu-nbd/dev
}

function _init-ubuntu20-img() {
    sudo mount -o bind /dev /mnt/qemu-nbd/dev
    sudo cp myinit/myinit.service /mnt/qemu-nbd/etc/systemd/system/
    sudo mkdir -p /mnt/qemu-nbd/opt/myinit/bin
    sudo cp myinit/myinit /mnt/qemu-nbd/opt/myinit/bin/myinit
    sudo chroot /mnt/qemu-nbd systemctl enable myinit.service

    sudo chroot /mnt/qemu-nbd apt remove -y cloud-init cloud-guest-utils cloud-initramfs-copymods cloud-initramfs-dyn-netconf

    # admin userの作成
    grep '^admin:' /mnt/qemu-nbd/etc/group || sudo chroot /mnt/qemu-nbd groupadd admin
    sudo chroot /mnt/qemu-nbd useradd -g admin -s /bin/bash admin
    echo 'admin:admin' | sudo chroot /mnt/qemu-nbd chpasswd
    sudo mkdir -p /mnt/qemu-nbd/home/admin
    sudo chroot /mnt/qemu-nbd chown -R admin:admin /home/admin
    sudo grep "%admin ALL=(ALL) ALL" /mnt/qemu-nbd/etc/sudoers || sudo sed -i '$ i %admin ALL=(ALL) ALL' /mnt/qemu-nbd/etc/sudoers

    sudo umount /mnt/qemu-nbd/dev
}

function custom-img() {
    set -ex
    cp ~/.cache/setup-scripts/images/$1 ~/.cache/setup-scripts/images/$1_custom
    name=$1_custom
    isCentos7=false
    isRocky8=false
    isUbuntu20=false
    if echo $1 | grep "centos7"; then
        isCentos7=true
    fi
    if echo $1 | grep "rocky8"; then
        isRocky8=true
    fi
    if echo $1 | grep "ubuntu20"; then
        isUbuntu20=true
    fi

    mount-qemu-nbd $name
    if "${isUbuntu20}"; then
        _init-ubuntu20-img
    fi
    if "${isCentos7}"; then
        _init-centos7-img
    fi
    if "${isRocky8}"; then
        _init-rocky8-img
    fi
    umount-qemu-nbd
}

$COMMAND
