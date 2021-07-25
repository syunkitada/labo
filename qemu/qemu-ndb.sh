#!/bin/bash -x

# qemu-nbdにより、nbd(network block device)経由で、qcow2などの仮想ディスクイメージを物理デバイスのように扱える

source envrc
source utilsrc

MOUNT_PATH=/mnt/qemu-nbd

COMMAND="${@:-help}"
function help() {
    cat << EOS
# mount qcow2 image by qemu-nbd
./qemu-nbd.sh mount-img [image_path]

# unmount qcow2 image
./qemu-nbd.sh umount-img

# list qemu-nbd process, and list mount path
./qemu-nbd.sh umount-img

# mount and init image for centos7
./qemu-nbd.sh int-centos7-img [image_path]
EOS
}

function mount-img() {
    if [ $# != 1 ]; then
        help
        exit 1
    fi
    path=$1

    test -e $path || (echo "file is not found: $path" && exit 1)

    sudo modprobe nbd max_part=63
    sudo mkdir -p $MOUNT_PATH
    sudo qemu-nbd -c /dev/nbd0 $path
    sudo mount /dev/nbd0p1 $MOUNT_PATH
}

function list() {
    set -xeo pipefail
    ps ax | grep qemu-nbd
    ls $MOUNT_PATH
}

function umount-img() {
    sudo umount $MOUNT_PATH
    sudo qemu-nbd --disconnect /dev/nbd0
    sudo rm -rf $MOUNT_PATH
}

function init-centos7-img() {
    if [ $# != 1 ]; then
        help
        exit 1
    fi
    mount-img $1

    sudo mount -o bind /dev /mnt/qemu-nbd/dev
    sudo cp myinit/myinit.service /mnt/qemu-nbd/etc/systemd/system/
    sudo mkdir -p /mnt/qemu-nbd/opt/myinit/bin
    sudo cp myinit/myinit /mnt/qemu-nbd/opt/myinit/bin/myinit
    sudo chroot /mnt/qemu-nbd systemctl enable myinit.service

    sudo chroot /mnt/qemu-nbd yum remove -y cloud-init

    sudo rm -rf /mnt/qemu-nbd/etc/sysconfig/network-scripts/ifcfg-eth0
    # 80-net-setup-link.rules があると、udevによって自動でifcfg-eth0を生成してしまうため削除する
    sudo rm -rf /mnt/qemu-nbd/lib/udev/rules.d/80-net-setup-link.rules

    sudo umount /mnt/qemu-nbd/dev

    umount-img
}

$COMMAND
