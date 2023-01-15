# メモ

## centos7 にインストール

```
sudo yum install -y https://repos.fedorapeople.org/repos/openstack/openstack-rocky/rdo-release-rocky-2.noarch.rpm

sudo yum install -y openvswitch libibverbs
sudo systemctl start openvswitch
sudo systemctl enable openvswitch
```

```
$ sudo ovs-vsctl show
14857e00-ec48-46cf-a2a9-147517cf7ec0
    ovs_version: "2.11.0"
```

## vm をつなげてみる

```
# bridgeの作成
sudo ovs-vsctl add-br br-ex
sudo ip link set br-ex up
sudo ip addr add 192.168.100.1/24 dev br-ex

virt-install \
--name vm2 --memory 2048 --cpu host --vcpus 2 \
--import --disk /tmp/vm2.qcow2,format=qcow2,bus=virtio \
--graphics none --network bridge=br-ex,model=virtio,virtualport_type=openvswitch

sudo ovs-vsctl show
14857e00-ec48-46cf-a2a9-147517cf7ec0
    Bridge br-ex
        Port "vnet0"
            Interface "vnet0"
        Port br-ex
            Interface br-ex
                type: internal
    ovs_version: "2.11.0"
```

## 制限まわり

- port(interface) name の長さは 15 までです
  - 参考: https://man7.org/linux/man-pages/man5/ovs-vswitchd.conf.db.5.html
  - add-port はいちおうできるが、flow の設定ができない

## オフロードまわり

- [DPDK Tunneling Offload](https://www.dpdk.org/wp-content/uploads/sites/35/2018/12/Rony_Yongseok_DPDK_Tunnel_Offloading.pdf)
- [2021-0708: OvS-DPDK Full VXLAN Offload with SR-IOV](https://www.openvswitch.org/support/ovscon2021/slides/ovs_dpdk_full_vxlan_offload.pdf)
