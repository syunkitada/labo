# ovs

```
yum install @'Development Tools' rpm-build yum-utils

git clone https://github.com/openvswitch/ovs.git
cd ovs
git checkout v2.7.0

./boot.sh
./configure

```

```
sed -e 's/@VERSION@/2.7.0/' rhel/openvswitch-fedora.spec.in > /tmp/ovs.spec
yum-builddep /tmp/ovs.spec
sudo yum install -y dpdk-devel libpcap-devel numactl-devel
make rpm-fedora RPMBUILD_OPT="--with dpdk --without check"
```

## debug

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

```
admin@local-vm1:~$ sudo docker exec clos1-HV1 ovs-appctl ofproto/trace br-int in_port=HV1_0_vm1,icmp,nw_src=10.100.0.1
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
