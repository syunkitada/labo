# clos1

## デバッグ

### br-ex から入った VM 宛ての通信のトレース

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

### br-int の VM からの通信のトレース

```
$ sudo docker exec clos1-HV1 ovs-appctl ofproto/trace br-int in_port=HV1_0_vm1,icmp,nw_src=10.100.0.2
Flow: icmp,in_port=1,vlan_tci=0x0000,dl_src=00:00:00:00:00:00,dl_dst=00:00:00:00:00:00,nw_src=10.100.0.1,nw_dst=0.0.0.0,nw_tos=0,nw_ecn=0,nw_ttl=0,nw_frag=no,icmp_type=0,icmp_code=0

bridge("br-int")
----------------
 0. ip,in_port=1,nw_src=10.100.0.1, priority 700
    output:2

bridge("br-ex")
---------------
 0. ip,in_port=5, priority 700
    group:1
     -> bucket 0: score 44846
     -> bucket 1: score 60326
     -> using bucket 1
    bucket 1
            set_field:00:16:3e:03:00:00->eth_dst
            output:3

Final flow: unchanged
Megaflow: recirc_id=0,eth,ip,in_port=1,dl_dst=00:00:00:00:00:00,nw_src=10.100.0.1,nw_dst=0.0.0.0,nw_frag=no
Datapath actions: set(eth(dst=00:16:3e:03:00:00)),4
```

### br-int の VM からの ARP のトレース

```
$ vmmac=00:16:3e:04:00:01
$ vmip=10.100.0.2
$ gateway=10.100.0.1
$ sudo docker exec clos1-HV1 ovs-appctl ofproto/trace br-int in_port=HV1_0_vm1,arp,arp_op=1,eth_src=${vmmac},arp_sha=${vmmac},arp_spa=${vmip},arp_tpa=${gateway}
Flow: arp,in_port=1,vlan_tci=0x0000,dl_src=00:16:3e:04:00:01,dl_dst=00:00:00:00:00:00,arp_spa=10.100.0.2,arp_tpa=10.100.0.1,arp_op=1,arp_sha=00:16:3e:04:00:01,arp_tha=00:00:00:00:00:00

bridge("br-int")
----------------
 0. arp,in_port=1,arp_op=1, priority 800
    move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[]
     -> NXM_OF_ETH_DST[] is now 00:16:3e:04:00:01
    set_field:00:16:3e:00:00:01->eth_src
    move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[]
     -> NXM_NX_ARP_THA[] is now 00:16:3e:04:00:01
    set_field:00:16:3e:00:00:01->arp_sha
    push:NXM_OF_ARP_TPA[]
    move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[]
     -> NXM_OF_ARP_TPA[] is now 10.100.0.2
    pop:NXM_OF_ARP_SPA[]
     -> NXM_OF_ARP_SPA[] is now 10.100.0.1
    set_field:2->arp_op
    IN_PORT

Final flow: arp,in_port=1,vlan_tci=0x0000,dl_src=00:16:3e:00:00:01,dl_dst=00:16:3e:04:00:01,arp_spa=10.100.0.1,arp_tpa=10.100.0.2,arp_op=2,arp_sha=00:16:3e:00:00:01,arp_tha=00:16:3e:04:00:01
Megaflow: recirc_id=0,eth,arp,in_port=1,dl_src=00:16:3e:04:00:01,dl_dst=00:00:00:00:00:00,arp_spa=10.100.0.2,arp_tpa=10.100.0.1,arp_op=1,arp_sha=00:16:3e:04:00:01,arp_tha=00:00:00:00:00:00
Datapath actions: set(eth(src=00:16:3e:00:00:01,dst=00:16:3e:04:00:01)),set(arp(sip=10.100.0.1,tip=10.100.0.2,op=2,sha=00:16:3e:00:00:01,tha=00:16:3e:04:00:01)),7
This flow is handled by the userspace slow path because it:
  - Uses action(s) not supported by datapath.
```
