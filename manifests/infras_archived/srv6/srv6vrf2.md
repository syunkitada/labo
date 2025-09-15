# srv6vrf2

- https://github.com/FRRouting/frr/tree/master/tests/topotests/bgp_srv6l3vpn_to_bgp_vrf
- https://github.com/FRRouting/frr/pull/5865
- https://github.com/FRRouting/frr/pull/9649

```
ip vrf exec vrf10 ping 10.100.0.2

srv6vrf2-HV1# show vrf
vrf vrf10 id 2 table 10

srv6vrf2-HV1# show ipv6 route
C>* fc06:0:1b:1401::/64 is directly connected, lo, 16:08:07
B>* fc06:0:1b:1401:a::/128 [20/0] is directly connected, vrf10, seg6local End.DT4 table 10, seg6 ::, weight 1, 16:08:06
B>* fc06:0:1b:1402::/64 [20/0] via fe80::216:3eff:fe00:1, HV1_0_HV2, weight 1, 04:23:10
C * fe80::/64 is directly connected, HV1_1_t2vm1, 16:08:07
C>* fe80::/64 is directly connected, HV1_0_HV2, 16:08:07


srv6vrf2-HV1# show segment-routing srv6 locator
Locator:
Name                 ID      Prefix                   Status
-------------------- ------- ------------------------ -------
default                    1 fc06:0:1b:1401::/64      Up

srv6vrf2-HV1# show ip route vrf vrf10
VRF vrf10:
C>* 10.100.0.0/24 is directly connected, HV1_0_t1vm1, 16:09:45
B>* 10.100.1.0/24 [20/0] via fe80::216:3eff:fe00:1, HV1_0_HV2 (vrf default), label 160, seg6local unspec unknown(seg6local_context2str), seg6 fc06:0:1b:1402:a::, weight 1, 04:24:48

srv6vrf2-HV2# show bgp segment-routing srv6
locator_name: default
locator_chunks:
- fc06:0:1b:1402::/64
  block-length: 40
  node-length: 24
  func-length: 16
  arg-length: 0
functions:
- sid: fc06:0:1b:1402:a::
  locator: default
bgps:
- name: default
  vpn_policy[AFI_IP].tovpn_sid: (null)
  vpn_policy[AFI_IP6].tovpn_sid: (null)
  per-vrf tovpn_sid: (null)
- name: vrf10
  vpn_policy[AFI_IP].tovpn_sid: fc06:0:1b:1402:a::
  vpn_policy[AFI_IP6].tovpn_sid: (null)
  per-vrf tovpn_sid: (null)


srv6vrf2-HV2# show ip route vrf all
VRF default:
B>* 10.10.20.1/32 [20/0] via fe80::216:3eff:fe00:0, HV2_0_HV1, weight 1, 00:10:24
C>* 10.10.20.2/32 is directly connected, lo, 00:10:26

VRF vrf10:
B>* 10.100.0.0/24 [20/0] via fe80::216:3eff:fe00:0, HV2_0_HV1 (vrf default), label 160, seg6local unspec unknown(seg6local_context2str), seg6 fc06:0:1b:1401:a::, weight 1, 00:10:24
C>* 10.100.1.0/24 is directly connected, HV2_0_t1vm2, 00:10:25



show ip bgp ipv4 neighbors HV2_0_HV1 advertised-routes


srv6vrf2-HV2# show ip bgp ipv4 vpn neighbors HV2_0_HV1 advertised-routes
    Network          Next Hop            Metric LocPrf Weight Path
Route Distinguisher: 0:10
 *> 10.100.0.0/24    0.0.0.0                                0 4201774593 ?
 *> 10.100.1.0/24    0.0.0.0                  0         32768 ?



srv6vrf2-HV2# show ip bgp ipv4 vpn neighbors HV2_0_HV1 routes
    Network          Next Hop            Metric LocPrf Weight Path
Route Distinguisher: 0:10
 *> 10.100.0.0/24    fe80::216:3eff:fe00:0
                                             0             0 4201774593 ?
    UN=fe80::216:3eff:fe00:0 EC{0:10} label=160 sid=fc06:0:1b:1401:: sid_structure=[40,24,16,0] type=bgp, subtype=0

Displayed  1 routes and 2 total paths
```
