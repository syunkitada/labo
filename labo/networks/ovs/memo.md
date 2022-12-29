# メモ

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
