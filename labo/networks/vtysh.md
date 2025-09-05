# vtysh

```
> show run
> show running-config
```

```
> show bgp summary
```

```
> show ip bgp

> show bgp
```

```
> show ip bgp neighbors
```

```
HV1.clos1# show ip bgp neighbors ADMIN advertised-routes
BGP table version is 2, local router ID is 10.10.10.2, vrf id 0
Default local pref 100, local AS 4201772034
Status codes:  s suppressed, d damped, h history, u unsorted, * valid, > best, = multipath,
               i internal, r RIB-failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

     Network          Next Hop            Metric LocPrf Weight Path
 *>  10.10.10.2/32    ::                       0         32768 i
```
