# frr2

- 3 段 CLOS 構成
- spine は 2 台で 1 セット、leaf も 2 台で１セットのアクティブアクティブ構成
- 各 spine は配下の各 leaf へそれぞれ配線される
- 各 leaf は配下の各 HV へそれぞれ配線される

## 構成

```
spine1[1-2] --- leaf1[1-2] --- hv111 --- vm1111
                           --- hv112
                           ...
            --- leaf2[1-2] --- hv121
                           --- hv122
                           ...

```

| name  | admin ip(router id) | as         |
| ----- | ------------------- | ---------- |
| hv111 | 10.1.10.111/32      | 4200110111 |
| hv112 | 10.1.10.112/32      | 4200110112 |
| hv121 | 10.1.10.121/32      | 4200110121 |
| hv122 | 10.1.10.122/32      | 4200110122 |
| lf111 | 10.1.20.11/32       | 4200120111 |
| lf112 | 10.1.20.12/32       | 4200120112 |
| lf121 | 10.1.20.21/32       | 4200120121 |
| lf122 | 10.1.20.22/32       | 4200120022 |
| sp11  | 10.1.30.11/32       | 4200130011 |
| sp12  | 10.1.30.12/32       | 4200130012 |

| name   | ip               |
| ------ | ---------------- |
| vm1111 | 192.168.200.2/24 |

# vm

```
ip addr add 192.168.200.2/24 dev hv111-vm1111-2
ip route add default via 192.168.200.1
```

# hv

```
ip link add vmbr type bridge
ip link set dev hv111-vm1111-1 master vmbr
ip addr add 192.168.200.1/24 dev vmbr
ip link set vmbr up
```

# hv frr

```
b# conf t
(config)# router bgp 4200110111
(config-router)# address-family ipv4 unicast
(config-router-af)# network 192.168.200.2/32
(config-router-af)# exit-address-family
(config-router)# exit
```
