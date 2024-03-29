# virt-install

## Enable kvm

```bash
% sudo modprobe kvm
% sudo modprobe kvm_intel
% sudo lsmod | grep kvm
kvm_intel             143590  0
kvm                   452043  1 kvm_intel

% sudo apt-get install libvirt-bin qemu
```

## Virt install

- 既存ディスクで起動

```
sudo yum -y install qemu-kvm qemu-img qemu-kvm-tools libvirt
sudo yum -y install virt-install wget
sudo systemctl start libvirtd
sudo systemctl enable libvirtd
wget http://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img
cp cirros-0.5.1-x86_64-disk.img /tmp/vm1.qcow2
virt-install  --name vm1 \
     --memory 2048  --cpu host --vcpus 2 --graphics none\
     --import  \
     --disk /tmp/vm1.qcow2,format=qcow2,bus=virtio \
     --network bridge=virbr0,model=virtio
```

- 新規ディスクで OS イメージから起動

```bash
# Create disk img of VM
$ sudo qemu-img create -f qcow2 /var/lib/libvirt/images/testvm 20G

# Create VM
$ sudo virt-install \
    --connect=qemu:///system \
    --name=testvm --vcpus=1 --ram=1024 \
    --accelerate --hvm --virt-type=kvm \
    --cpu host \
    --disk=/var/lib/libvirt/images/testvm.img,format=qcow2 \
    --location='/tmp/imgs/CentOS-6.6-x86_64-bin-DVD1.iso' \
    --nographics \
    --extra-args='console=tty0 console=ttyS0,115200n8 keymap=ja'
```

## 便利コマンド

```bash
# Create Snapshot
$ sudo virsh snapshot-create-as testvm testsnap 'first snap'

$ sudo virsh snapshot-list testvm
 Name                 Creation Time             State
 ------------------------------------------------------------
  testsnap             2015-06-21 11:58:35 +0900 running

$ sudo virsh snapshot-revert testvm testsnap

$ sudo virsh snapshot-info testvm testsnap
Name:           testsnap
Domain:         testvm
Current:        yes
State:          running
Location:       internal
Parent:         -
Children:       0
Descendants:    0
Metadata:       yes

$ sudo virsh snapshot-info testvm --current
Name:           testsnap
Domain:         testvm
Current:        yes
State:          running
Location:       internal
Parent:         -
Children:       0
Descendants:    0
Metadata:       yes

$ sudo virsh snapshot-dumpxml vm1 snap1

$ sudo virsh snapshot-delete vm1 snap1
```

## Virt clone

```bash
$ sudo virt stop centos7dev1
$ sudo virt-clone -o centos7dev1 -n centos7dev2 -f /opt/imgs/centos7dev2.img
```

## Booting cloud image with libvirt

```
$ vim meta-data
> instance-id: my-instance-id
> local-hostname: my-host-name

$ vim user-data
> #!/bin/sh
>
> echo 'hello world' > /etc/fstab
> apt-get install -y sudo passwd openssh-server
>
> mkdir /var/run/sshd
>
> useradd fabric -d /home/fabric
> gpasswd --add fabric sudo
> mkdir /home/fabric
> chown fabric:fabric /home/fabric
> echo 'fabric:fabric' |chpasswd

$ sudo genisoimage -o config.iso -V cidata -r -J meta-data user-data

$ sudo virt-install \
    --connect=qemu:///system \
    --name=testvm --vcpus=1 --ram=1024 \
    --accelerate --hvm --virt-type=kvm \
    --cpu host \
    --disk ubuntu14.img,format=qcow2 --import \
    --disk config.iso,device=cdrom \
    --nographics
```

参考

- http://blog.oddbit.com/2015/03/10/booting-cloud-images-with-libvirt/
