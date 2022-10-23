# qemu

## image のリサイズ

```
$ sudo qemu-img info ~/.cache/setup-scripts/vms/ubuntu20-small1.example.com/img
image: /home/owner/.cache/setup-scripts/vms/ubuntu20-small1.example.com/img
file format: qcow2
virtual size: 20 GiB (21474836480 bytes)
disk size: 1.31 GiB
cluster_size: 65536
Format specific information:
    compat: 0.10
    refcount bits: 16

$ sudo qemu-img resize --shrink ~/.cache/setup-scripts/vms/ubuntu20-small1.example.com/img 40G

$ sudo qemu-img info ~/.cache/setup-scripts/vms/ubuntu20-small1.example.com/img
image: /home/owner/.cache/setup-scripts/vms/ubuntu20-small1.example.com/img
file format: qcow2
virtual size: 40 GiB (42949672960 bytes)
disk size: 1.31 GiB
cluster_size: 65536
Format specific information:
    compat: 0.10
    refcount bits: 16
```

- ブロックサイズを変更した後は、ファイルシステム側も拡張する必要がある
- ubuntu20 の場合は以下

```
$ lsblk
NAME    MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0     7:0    0 55.4M  1 loop /snap/core18/2066
loop1     7:1    0 32.3M  1 loop /snap/snapd/12159
loop2     7:2    0 67.6M  1 loop /snap/lxd/20326
sr0      11:0    1  366K  0 rom
vda     252:0    0   20G  0 disk
├─vda1  252:1    0  2.1G  0 part /
├─vda14 252:14   0    4M  0 part
└─vda15 252:15   0  106M  0 part /boot/efi

$ sudo parted /dev/vda
GNU Parted 3.3
Using /dev/vda
Welcome to GNU Parted! Type 'help' to view a list of commands.
(parted) p free
Warning: Not all of the space available to /dev/vda appears to be used, you can fix the GPT to use all of the space (an extra 37330944 blocks) or continue
with the current setting?
Fix/Ignore? Fix
Model: Virtio Block Device (virtblk)
Disk /dev/vda: 21.5GB
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:

Number  Start   End     Size    File system  Name  Flags
        17.4kB  1049kB  1031kB  Free Space
        14      1049kB  5243kB  4194kB                     bios_grub
        15      5243kB  116MB   111MB   fat32              boot, esp
         1      116MB   2361MB  2245MB  ext4
                 2361MB  21.5GB  19.1GB  Free Space

                 (parted) resizepart 1
                 Warning: Partition /dev/vda1 is being used. Are you sure you want to continue?
                 Yes/No? yes
                 End?  [2361MB]? 100%
                 (parted) p free
                 Model: Virtio Block Device (virtblk)
                 Disk /dev/vda: 21.5GB
                 Sector size (logical/physical): 512B/512B
                 Partition Table: gpt
                 Disk Flags:

                 Number  Start   End     Size    File system  Name  Flags
                         17.4kB  1049kB  1031kB  Free Space
                         14      1049kB  5243kB  4194kB                     bios_grub
                         15      5243kB  116MB   111MB   fat32              boot, esp
                          1      116MB   21.5GB  21.4GB  ext4

(parted) quit
Information: You may need to update /etc/fstab.

$ sudo resize2fs /dev/vda1
```

## cidata のマウント

```
[admin@centos7-1 ~]$ sudo mkdir -p /mnt/cidata
[admin@centos7-1 ~]$ sudo mount /dev/disk/by-label/cidata /mnt/cidata
mount: /dev/sr0 is write-protected, mounting read-only
```

## MAC アドレスの生成について

- https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/virtualization_administration_guide/sect-virtualization-tips_and_tricks-generating_a_new_unique_mac_address
- https://github.com/rlaager/python-virtinst/blob/b75a3b9d45053499908915b4daf4dab2bc95cbce/virtinst/util.py#L177
- https://standards-oui.ieee.org/oui36/oui36.txt
- xen: 00:16:3E:XX:XX:XX
- qemu: 52:54:00:XX:XX:XX

## nested

```
$ cat /sys/module/kvm_amd/parameters/nested
1
```

## 参考

- [qemu](https://manpages.debian.org/testing/qemu-system-x86/qemu-system-x86_64.1.en.html)
- [第 12 章 qemu-kvm を利用した仮想マシンの実行](https://manual.geeko.jp/ja/cha.qemu.running.html)
- [第 13 章 QEMU モニタを利用した仮想マシンの管理](https://manual.geeko.jp/ja/cha.qemu.monitor.html)
