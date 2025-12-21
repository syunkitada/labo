# Configuration

## Enable nested virtualization for AMD processors

```
$ cat /sys/module/kvm_amd/parameters/nested
1
```

## Config Drive

### cidata のマウント

```
[admin@centos7-1 ~]$ sudo mkdir -p /mnt/cidata
[admin@centos7-1 ~]$ sudo mount /dev/disk/by-label/cidata /mnt/cidata
mount: /dev/sr0 is write-protected, mounting read-only
```

## MAC アドレスの生成方法

- https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/virtualization_administration_guide/sect-virtualization-tips_and_tricks-generating_a_new_unique_mac_address
- https://github.com/rlaager/python-virtinst/blob/b75a3b9d45053499908915b4daf4dab2bc95cbce/virtinst/util.py#L177
- https://standards-oui.ieee.org/oui36/oui36.txt
- xen: 00:16:3E:XX:XX:XX
- qemu: 52:54:00:XX:XX:XX
