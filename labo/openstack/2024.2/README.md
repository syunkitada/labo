# OpenStack

```
$ make
```

```
$ sudo docker exec -it openstack-2024-2 bash
[root@openstack-allinone /]#

[root@openstack-allinone /]# source /opt/openstack/adminrc

[root@openstack-allinone /]# openstack server create --net local-net --image cirros --flavor 1v-512M-1G testvm

[root@openstack-allinone /]# openstack server list
+--------------------------------------+--------+--------+-------------------------+--------+------------+
| ID                                   | Name   | Status | Networks                | Image  | Flavor     |
+--------------------------------------+--------+--------+-------------------------+--------+------------+
| bdae2186-81e5-45c5-8498-221f284e1b1a | testvm | ACTIVE | local-net=192.168.0.222 | cirros | 1v-512M-1G |
+--------------------------------------+--------+--------+-------------------------+--------+------------+

[root@openstack-allinone /]# openstack server delete bdae2186-81e5-45c5-8498-221f284e1b1a

[root@openstack-allinone /]# openstack server list
+--------------------------------------+--------+---------+----------+--------+------------+
| ID                                   | Name   | Status  | Networks | Image  | Flavor     |
+--------------------------------------+--------+---------+----------+--------+------------+
| bdae2186-81e5-45c5-8498-221f284e1b1a | testvm | DELETED |          | cirros | 1v-512M-1G |
+--------------------------------------+--------+---------+----------+--------+------------+

[root@openstack-allinone /]# openstack server list

[root@openstack-allinone /]#
```
