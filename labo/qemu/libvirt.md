# libvirt

```
$ sudo virsh sysinfo | grep uuid

$ sudo virsh capabilities | grep uuid

$ sudo dmidecode | grep -i uuid
        UUID: c00017b6-f84d-0000-0000-000000000000

host_uuid
```

```
virsh -c test+ssh://root@host/default list

virsh -c .... migrate --live hoge ...
```
