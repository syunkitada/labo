# VM

```
$ sudo uv run mylabo apply -f manifests/infras/vm/rocky9.yml
```

```
$ virsh list --all
 Id   Name                     State
-----------------------------------------
 1    VM1.rocky9.mylabo.test   running
```

```
$ virsh console VM1.rocky9.mylabo.test
Connected to domain 'VM1.rocky9.mylabo.test'
Escape character is ^] (Ctrl + ])

VM1 login: admin
Password: <admin>
Last login: Mon Nov 24 05:08:24 on ttyS0
[admin@VM1 ~]$
```

```
[admin@VM1 ~]$ sudo mkdir /mnt/nfs
[admin@VM1 ~]$ sudo mount -t nfs 192.168.10.121:/ /mnt/nfs
[  488.700767] FS-Cache: Loaded
[  488.783138] Key type dns_resolver registered
[  488.971882] NFS: Registering the id_resolver key type
[  488.971905] Key type id_resolver registered
[  488.971914] Key type id_legacy registered
```
