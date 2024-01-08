# image

```
$ sudo virt-filesystems --long --parts --blkdevs -h -a /tmp/ubuntu22_custom.tmp
Name        Type       MBR  Size  Parent
/dev/sda1   partition  -    2.1G  /dev/sda
/dev/sda14  partition  -    4.0M  /dev/sda
/dev/sda15  partition  -    106M  /dev/sda
/dev/sda    device     -    2.2G  -
```

## 参考

- https://docs.openstack.org/ja/image-guide/modify-images.html
- [How to fix partition table after virt-resize rearranges it (KVM)?](https://serverfault.com/questions/976792/how-to-fix-partition-table-after-virt-resize-rearranges-it-kvm)
