# SRv6 with VRF

## Check ping from t1vm1 to t1vm2 on SRv6 tunnel

```
$ docker exec -it t1vm1.srv6vrf ping 10.100.1.3
PING 10.100.1.3 (10.100.1.3) 56(84) bytes of data.
64 bytes from 10.100.1.3: icmp_seq=1 ttl=63 time=0.171 ms
64 bytes from 10.100.1.3: icmp_seq=2 ttl=63 time=0.229 ms
^C
```

## Check VRFs

```
[root@HV1 /]# ip vrf show
Name              Table
-----------------------
vrf50               50

# Ping to t1vm1 on vrf50
[root@HV1 /]# ip vrf exec vrf50 ping 10.100.1.2
PING 10.100.1.2 (10.100.1.2) 56(84) bytes of data.
64 bytes from 10.100.1.2: icmp_seq=1 ttl=64 time=0.067 ms
64 bytes from 10.100.1.2: icmp_seq=2 ttl=64 time=0.050 ms
```

## Check routes for SRv6

```
# If vrf50 on HV1 send to 10.100.1.3(t1vm2 on HV2), encap with SRv6 and send to fc06:0:1b:1403::50(HV2)
[root@HV1 /]# ip route list vrf vrf50
10.100.1.0/24 dev HV1_0_t1vm1 proto kernel scope link src 10.100.1.1
10.100.1.2 dev HV1_0_t1vm1 scope link
10.100.1.3  encap seg6 mode encap segs 1 [ fc06:0:1b:1403::50 ] dev HV1_0_L11 scope link

# If HV2 receive to fc06:0:1b:1403::50, decap with SRv6 and send to vrf50
[root@HV2 /]# ip -6 route show table localsid
fc06:0:1b:1403::50  encap seg6local action End.DX4 nh4 169.254.1.50 dev vrf50 metric 1024 pref medium
blackhole default dev lo metric 1024 pref medium

# If vrf50 on HV2 receive to 10.100.1.3, send to t1vm2
[root@HV2 /]# ip route list vrf vrf50
10.100.1.0/24 dev HV2_0_t1vm2 proto kernel scope link src 10.100.1.1
10.100.1.2  encap seg6 mode encap segs 1 [ fc06:0:1b:1402::50 ] dev HV2_0_L21 scope link
10.100.1.3 dev HV2_0_t1vm2 scope link
```

## Check vtysh

```
[root@HV1 /]# vtysh
```

### Check bgp summary

```
HV1.srv6vrf# show ip bgp summary
Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
HV1_0_L11       4 4201769986        45        46        9    0    0 00:29:56            8        9 N/A
```

### Check ip route

```
HV1.srv6vrf# show ipv6 route
IPv6 unicast VRF default:
B>* fc00::10:10:0:0/112 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:02:54
C>* fc06:0:1b:1402::/64 is directly connected, lo, weight 1, 00:02:56
L>* fc06:0:1b:1402::1/128 is directly connected, lo, weight 1, 00:02:56
B>* fc06:0:1b:1403::/64 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:02:41
C * fe80::/64 is directly connected, HV1_1_t2vm1, weight 1, 00:02:56
C>* fe80::/64 is directly connected, HV1_0_L11, weight 1, 00:02:56
```

### Check ip route on VRF

```
HV1.srv6vrf# show vrf
vrf vrf50 id 2 table 50

HV1.srv6vrf# show ip route vrf vrf50
IPv4 unicast VRF vrf50:
C>* 10.100.1.0/24 is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:24:36
K * 10.100.1.0/24 [0/0] is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:24:42
L>* 10.100.1.1/32 is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:24:36
K>* 10.100.1.2/32 [0/0] is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:24:42
K>* 10.100.1.3/32 [0/0] is directly connected, HV1_0_L11 (vrf default), seg6 fc06:0:1b:1403::50, weight 1, 00:24:42

HV1.srv6vrf# show ip route vrf all
IPv4 unicast VRF default:
B>* 10.10.0.0/24 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
B>* 10.10.1.3/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
B>* 10.10.1.4/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
B>* 10.10.2.2/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
B>* 10.10.2.3/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
B>* 10.10.2.4/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
B>* 10.10.2.5/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:26
L * 10.10.20.2/32 is directly connected, lo, weight 1, 00:26:29
C>* 10.10.20.2/32 is directly connected, lo, weight 1, 00:26:29
B>* 10.10.20.3/32 [20/0] via fe80::216:3eff:fe04:0, HV1_0_L11, weight 1, 00:26:19
K>* 169.254.1.50/32 [0/0] is directly connected, vrf50 (vrf vrf50), weight 1, 00:26:23

IPv4 unicast VRF vrf50:
C>* 10.100.1.0/24 is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:26:17
K * 10.100.1.0/24 [0/0] is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:26:23
L>* 10.100.1.1/32 is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:26:17
K>* 10.100.1.2/32 [0/0] is directly connected, HV1_0_t1vm1 linkdown, weight 1, 00:26:23
K>* 10.100.1.3/32 [0/0] is directly connected, HV1_0_L11 (vrf default), seg6 fc06:0:1b:1403::50, weight 1, 00:26:23
```

### Check advertised-routes

```
HV1.srv6vrf# show ip bgp ipv4 neighbors ADMIN advertised-routes
     Network          Next Hop            Metric LocPrf Weight Path
 *>  10.10.0.0/24     HV1_0_L11                              0 4201769986 4201769732 4201769730 i
 *>  10.10.1.3/32     HV1_0_L11                              0 4201769986 4201769731 i
 *>  10.10.1.4/32     HV1_0_L11                              0 4201769986 4201769732 i
 *>  10.10.2.2/32     HV1_0_L11                              0 4201769986 i
 *>  10.10.2.3/32     HV1_0_L11                              0 4201769986 4201769731 4201769987 i
 *>  10.10.2.4/32     HV1_0_L11                              0 4201769986 4201769731 4201769988 i
 *>  10.10.2.5/32     HV1_0_L11                              0 4201769986 4201769731 4201769989 i
 *>  10.10.20.2/32    ::                       0         32768 i
 *>  10.10.20.3/32    HV1_0_L11                              0 4201769986 4201769731 4201769988 4201774595 i
```

```
HV1.srv6vrf# show ip bgp ipv6 neighbors ADMIN advertised-routes
     Network          Next Hop            Metric LocPrf Weight Path
 *>  fc00::10:10:0:0/112
                    HV1_0_L11                              0 4201769986 4201769732 4201769730 i
 *>  fc06:0:1b:1402::/64
                    ::                       0         32768 i
 *>  fc06:0:1b:1403::/64
                    HV1_0_L11                              0 4201769986 4201769731 4201769988 4201774595 i
```
