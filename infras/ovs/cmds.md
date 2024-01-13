# CLI コマンド一覧

## ブリッジ構成の表示

```
$ sudo docker exec -it clos1-HV1 ovs-vsctl show
bc78271d-16db-4f55-b12e-4cfc327e13cb
    Bridge br-int
        datapath_type: netdev
        Port br-int
            Interface br-int
                type: internal
        Port HV1_0_vm1
            Interface HV1_0_vm1
        Port br-int_br-ex
            Interface br-int_br-ex
                type: patch
                options: {peer=br-ex_br-int}
    Bridge br-ex
        datapath_type: netdev
        Port br-ex
            Interface br-ex
                type: internal
        Port HV1_0_L12.200
            Interface HV1_0_L12.200
        Port HV1_0_L11.200
            Interface HV1_0_L11.200
        Port br-ex-bgp1
            Interface br-ex-bgp1
        Port br-ex-bgp0
            Interface br-ex-bgp0
        Port br-ex_br-int
            Interface br-ex_br-int
                type: patch
                options: {peer=br-int_br-ex}
    ovs_version: "2.17.4"
```

## port の一覧表示

```
$ sudo docker exec clos1-HV1 ovs-ofctl show br-int
OFPT_FEATURES_REPLY (xid=0x2): dpid:000000163e040000
n_tables:254, n_buffers:0
capabilities: FLOW_STATS TABLE_STATS PORT_STATS QUEUE_STATS ARP_MATCH_IP
actions: output enqueue set_vlan_vid set_vlan_pcp strip_vlan mod_dl_src mod_dl_dst mod_nw_src mod_nw_dst mod_nw_tos mod_tp_src mod_tp_dst
 1(HV1_0_vm1): addr:00:16:3e:04:00:00
     config:     0
     state:      0
     current:    10GB-FD COPPER
     speed: 10000 Mbps now, 0 Mbps max
 2(br-int_br-ex): addr:2a:cd:09:16:5d:e5
     config:     0
     state:      0
     speed: 0 Mbps now, 0 Mbps max
 LOCAL(br-int): addr:00:16:3e:04:00:00
     config:     0
     state:      0
     current:    10MB-FD COPPER
     speed: 10 Mbps now, 0 Mbps max
OFPT_GET_CONFIG_REPLY (xid=0x4): frags=normal miss_send_len=0
```

## port stat の一覧表示

```
$ sudo docker exec -it clos1-HV1 ovs-ofctl dump-ports br-int
OFPST_PORT reply (xid=0x2): 3 ports
  port LOCAL: rx pkts=8, bytes=896, drop=0, errs=0, frame=0, over=0, crc=0
           tx pkts=0, bytes=0, drop=0, errs=0, coll=0
  port  "HV1_0_vm1": rx pkts=9, bytes=886, drop=0, errs=0, frame=0, over=0, crc=0
           tx pkts=9, bytes=886, drop=0, errs=0, coll=0
  port  "br-int_br-ex": rx pkts=1, bytes=98, drop=?, errs=?, frame=?, over=?, crc=?
           tx pkts=2, bytes=228, drop=?, errs=?, coll=?
```

## bridge のフローの表示

```
$ sudo docker exec -it clos1-HV1 ovs-ofctl dump-flows br-ex
 cookie=0x0, duration=1071.620s, table=0, n_packets=112, n_bytes=13920, priority=800,ipv6,in_port="HV1_0_L11.200",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"br-ex-bgp0"
 cookie=0x0, duration=1071.620s, table=0, n_packets=120, n_bytes=12081, priority=800,ipv6,in_port="br-ex-bgp0",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"HV1_0_L11.200"
 cookie=0x0, duration=1071.619s, table=0, n_packets=107, n_bytes=13419, priority=800,ipv6,in_port="HV1_0_L12.200",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"br-ex-bgp1"
 cookie=0x0, duration=1071.619s, table=0, n_packets=118, n_bytes=11897, priority=800,ipv6,in_port="br-ex-bgp1",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"HV1_0_L12.200"
 cookie=0x0, duration=1071.619s, table=0, n_packets=146, n_bytes=11396, priority=800,ipv6,in_port="HV1_0_L11.200",ipv6_dst=ff02::/16 actions=output:"br-ex-bgp0"
 cookie=0x0, duration=1071.618s, table=0, n_packets=111, n_bytes=8826, priority=800,ipv6,in_port="br-ex-bgp0",ipv6_dst=ff02::/16 actions=output:"HV1_0_L11.200"
 cookie=0x0, duration=1071.618s, table=0, n_packets=146, n_bytes=11396, priority=800,ipv6,in_port="HV1_0_L12.200",ipv6_dst=ff02::/16 actions=output:"br-ex-bgp1"
 cookie=0x0, duration=1071.618s, table=0, n_packets=111, n_bytes=8826, priority=800,ipv6,in_port="br-ex-bgp1",ipv6_dst=ff02::/16 actions=output:"HV1_0_L12.200"
 cookie=0x0, duration=650.383s, table=0, n_packets=0, n_bytes=0, priority=700,ip,in_port="HV1_0_L11.200" actions=output:"br-ex_br-int"
 cookie=0x0, duration=650.382s, table=0, n_packets=1, n_bytes=98, priority=700,ip,in_port="br-ex_br-int" actions=group:1
 cookie=0x0, duration=650.381s, table=0, n_packets=1, n_bytes=98, priority=700,ip,in_port="HV1_0_L12.200" actions=output:"br-ex_br-int"
 cookie=0x0, duration=1071.618s, table=0, n_packets=10, n_bytes=1112, priority=0 actions=drop
```

```
# カウンタを表示させたくない場合は、--no-stats を付けます
$ sudo docker exec -it clos1-HV1 ovs-ofctl dump-flows br-ex --no-stats
 priority=800,ipv6,in_port="HV1_0_L11.200",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"br-ex-bgp0"
 priority=800,ipv6,in_port="br-ex-bgp0",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"HV1_0_L11.200"
 priority=800,ipv6,in_port="HV1_0_L12.200",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"br-ex-bgp1"
 priority=800,ipv6,in_port="br-ex-bgp1",ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:"HV1_0_L12.200"
 priority=800,ipv6,in_port="HV1_0_L11.200",ipv6_dst=ff02::/16 actions=output:"br-ex-bgp0"
 priority=800,ipv6,in_port="br-ex-bgp0",ipv6_dst=ff02::/16 actions=output:"HV1_0_L11.200"
 priority=800,ipv6,in_port="HV1_0_L12.200",ipv6_dst=ff02::/16 actions=output:"br-ex-bgp1"
 priority=800,ipv6,in_port="br-ex-bgp1",ipv6_dst=ff02::/16 actions=output:"HV1_0_L12.200"
 priority=700,ip,in_port="HV1_0_L11.200" actions=output:"br-ex_br-int"
 priority=700,ip,in_port="br-ex_br-int" actions=group:1
 priority=700,ip,in_port="HV1_0_L12.200" actions=output:"br-ex_br-int"
 priority=0 actions=drop
```

## bridge のグループを表示

```
$ sudo docker exec -it clos1-HV1 ovs-ofctl dump-groups br-ex
NXST_GROUP_DESC reply (xid=0x2):
 group_id=1,type=select,selection_method=hash,fields(ip_src,ip_dst),bucket=bucket_id:0,watch_port:"HV1_0_L11.200",actions=mod_dl_dst:00:16:3e:02:00:00,output:"HV1_0_L11.200",bucket=bucket_id:1,watch_port:"HV1_0_L12.200",actions=mod_dl_dst:00:16:3e:03:00:00,output:"HV1_0_L12.200"
```

```
$ sudo docker exec -it clos1-HV1 ovs-ofctl dump-group-stats br-ex --no-stats
NXST_GROUP reply (xid=0x6):
 group_id=1,duration=1236.681s,ref_count=1,packet_count=1,byte_count=98,bucket0:packet_count=1,byte_count=98,bucket1:packet_count=0,byte_count=0
```

## パケットフローのトレース

```
$ sudo docker exec clos1-HV1 ovs-appctl ofproto/trace br-ex in_port=HV1_0_L11.200,icmp,nw_dst=10.100.0.1
Flow: icmp,in_port=1,vlan_tci=0x0000,dl_src=00:00:00:00:00:00,dl_dst=00:00:00:00:00:00,nw_src=0.0.0.0,nw_dst=10.100.0.1,nw_tos=0,nw_ecn=0,nw_ttl=0,nw_frag=no,icmp_type=0,icmp_code=0

bridge("br-ex")
---------------
 0. ip,in_port=1, priority 700
    output:5

bridge("br-int")
----------------
 0. ip,in_port=2,nw_dst=10.100.0.1, priority 700
    set_field:00:16:3e:00:00:01->eth_dst
    output:1

Final flow: unchanged
Megaflow: recirc_id=0,eth,ip,in_port=1,dl_dst=00:00:00:00:00:00,nw_dst=10.100.0.1,nw_frag=no
Datapath actions: set(eth(dst=00:16:3e:00:00:01)),7
```

## ロギング

```
# ログの設定を確認
$ sudo docker exec -it clos1-HV1 ovs-appctl vlog/list

# ログレベルを変更する
$ sudo docker exec -it clos1-HV1 ovs-appctl vlog/set file::dbg
$ sudo docker exec -it clos1-HV1 ovs-appctl vlog/set file::info
```

## ルートの確認

```
$ sudo docker exec -it clos1-HV1 ovs-appctl ovs/route/show
Route Table:
Cached: 10.10.3.2/32 dev HV1_0_L11 SRC 10.10.3.2 local
Cached: 10.10.10.1/32 dev l3admin SRC 10.10.10.1 local
Cached: 127.0.0.1/32 dev lo SRC 127.0.0.1 local
Cached: 169.254.0.2/32 dev HV1_0_L12.100 SRC 169.254.0.2 local
Cached: ::1/128 dev lo SRC ::1 local
Cached: fe80::216:3eff:fe02:1/128 dev br-ex SRC fe80::216:3eff:fe02:1 local
Cached: fe80::216:3eff:fe03:1/128 dev HV1_0_L12.100 SRC fe80::216:3eff:fe03:1 local
Cached: fe80::216:3eff:fe04:0/128 dev HV1_0_vm1 SRC fe80::216:3eff:fe04:0 local
Cached: fe80::307e:d8ff:fe84:a33f/128 dev bgp0 SRC fe80::307e:d8ff:fe84:a33f local
Cached: fe80::482c:b1ff:fe36:fc2b/128 dev br-ex-bgp0 SRC fe80::482c:b1ff:fe36:fc2b local
Cached: fe80::8c71:16ff:fe70:778f/128 dev br-ex-bgp1 SRC fe80::8c71:16ff:fe70:778f local
Cached: fe80::94a3:b9ff:fef1:8bfe/128 dev l3admin SRC fe80::94a3:b9ff:fef1:8bfe local
Cached: fe80::d4f5:35ff:fe70:bc9d/128 dev bgp1 SRC fe80::d4f5:35ff:fe70:bc9d local
Cached: 127.0.0.0/8 dev lo SRC 127.0.0.1 local
Cached: 10.10.3.0/27 dev HV1_0_L11 SRC 10.10.3.2
Cached: 169.254.0.0/24 dev HV1_0_L12.100 SRC 169.254.0.2
Cached: 0.0.0.0/0 dev HV1_0_L11 GW 10.10.3.1 SRC 10.10.3.2
Cached: fe80::/64 dev HV1_0_vm1 SRC fe80::216:3eff:fe04:0
```

```
# ovs-appctl ovs/route/lookup 10.10.2.2
src 10.10.1.2
gateway 10.10.1.1
dev br-ex
```
