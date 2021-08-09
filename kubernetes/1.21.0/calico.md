# calico

- [calico](https://docs.projectcalico.org/about/about-calico)

- Calico は 2014 年に Metaswitch Networks 社によって OSS プロジェクトとして発表され、GitHub 上でソースコードが公開されました
- 現在は、CoreOS 社（後に Red Hat に買収された）とともに設立された Tigera 社が Calico の開発を主導している

## Calico Operator(Tigera Operator)

- https://github.com/tigera/operator

```
$ kubectl get pod -n tigera-operator
NAME                               READY   STATUS    RESTARTS   AGE
tigera-operator-698876cbb5-m985v   1/1     Running   1          52m
```

## calicoctl

```
# ipamの表示
$ calicoctl ipam show
+----------+---------------+-----------+------------+--------------+
| GROUPING |     CIDR      | IPS TOTAL | IPS IN USE |   IPS FREE   |
+----------+---------------+-----------+------------+--------------+
| IP Pool  | 10.200.0.0/16 |     65536 | 4 (0%)     | 65532 (100%) |
+----------+---------------+-----------+------------+--------------+
```

```
# nodeのステータス表示
$ sudo calicoctl node status
Calico process is running.

IPv4 BGP status
No IPv4 peers found.

IPv6 BGP status
No IPv6 peers found.
```

```
# nodeの一覧表示
$ calicoctl get node -o wide
NAME                         ASN       IPV4               IPV6
centos7-small1.example.com   (64512)   192.168.100.2/24
```

```
# pod名とcalicoのインターフェイスを表示する
$ calicoctl get workloadEndpoint
WORKLOAD                           NODE                         NETWORKS            INTERFACE
nginx-deployment-585449566-bbjfz   centos7-small1.example.com   10.200.155.194/32   cali0b4f99fe5ba
```
