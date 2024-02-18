# bobcat

```
sudo -E fab make -f infras/openstack/bobcat.yaml
```

```
sudo docker exec -it bobcat-allinone bash
source /etc/adminrc
openstack server create --flavor 1v-1024m-5g --image cirros --net local-net testvm1

openstack server list
+--------------------------------------+---------+--------+-------------------------+--------+-------------+
| ID                                   | Name    | Status | Networks                | Image  | Flavor      |
+--------------------------------------+---------+--------+-------------------------+--------+-------------+
| 9c72b90d-4c1b-420e-bf7f-894ae4ce102e | testvm1 | ACTIVE | local-net=192.168.0.146 | cirros | 1v-1024m-5g |
+--------------------------------------+---------+--------+-------------------------+--------+-------------+
```
