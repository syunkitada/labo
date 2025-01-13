# OpenStack

```
$ make
```

```
$ sudo docker exec -it openstack-2024-2 bash
[root@openstack-allinone /]#

[root@openstack-allinone /]# source /opt/openstack/adminrc

[root@openstack-allinone /]# openstack server create --net local-net --image cirros --flavor 1v-512M-1G testvm
```
