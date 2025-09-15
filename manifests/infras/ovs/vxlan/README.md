# vxlan

## デバッグ

### dump flows

```
[root@HV1 /]# ovs-ofctl dump-flows br-ex
...
[root@HV1 /]# ovs-ofctl dump-flows br-t1
...
[root@HV1 /]# ovs-ofctl dump-flows br-t1-int
 cookie=0x0, duration=481.664s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
```
