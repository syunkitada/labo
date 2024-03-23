# openstack-bobcat

```
$ sudo -E docker compose up -d
```

```
# If you want to change name_prefix of docker container, set NAMESPACE environment variable
$ export NAMESPACE=hoge
$ sudo -E docker compose up -d
```

```
$ kind create cluster --config kind.yml

$ kind get clusters
kind

$ docker exec -i openstack-bobcat-ansible mkdir -p /root/.kube/
$ kind get kubeconfig -n kind | sed -e 's|server: .*|server: https://kind-control-plane:6443|g' | sudo docker exec -i openstack-bobcat-ansible tee /root/.kube/config

# $ kind export -n kind kubeconfig
# $ kind delete cluster -n openstack-bobcat
```

```
$ sudo docker exec -it openstack-bobcat-ansible bash
$ cd /etc/ansible/inventories/
$ ansible-playbook -i ctl_hosts.yml labo.openstack_bobcat.ctl
$ ansible-playbook -i hv_hosts.yml -i hv_az1_hosts.yml labo.openstack_bobcat.hv
$ ansible-playbook -i ctl_hosts.yml labo.openstack_bobcat.ctl --tags cmd_nova_discover_hosts
```

```
$ openstack server create --flavor 1v-1024m-5g --image cirros --no-network --os-compute-api-version 2.37 testvm1
```
