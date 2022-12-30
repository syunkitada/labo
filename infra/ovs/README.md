# OVS (Open vSwitch)

## ヘルプ・ドキュメント類

- 公式ドキュメント
  - https://docs.openvswitch.org/en/latest/
- ovs-vsctl
  - ovsdb-server と通信してブリッジ構成の確認・操作をするための CLI です
  - http://www.openvswitch.org/support/dist-docs/ovs-vsctl.8.html
  - $ ovs-vsctl -h
- ovs-ofctl
  - ovsdb-server と通信してブリッジの openflow の確認・操作をするための CLI です
  - http://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.html
  - $ ovs-ofctl -h
- ovs-appctl
  - vswitchd と通信していろいろ操作するための CLI です
  - https://docs.openvswitch.org/en/latest/ref/ovs-appctl.8/
  - $ ovs-appctl list-commands
    - ovs-appctl は、-h だと対して情報がなく、list-commands で利用可能なコマンドを確認するとよい
- ovs-actions
  - openflow で利用できる actions のドキュメント
  - https://docs.openvswitch.org/en/latest/ref/ovs-actions.7/
- ovs-fields
  - openflow で利用できる fields のドキュメント
  - http://www.openvswitch.org/support/dist-docs/ovs-fields.7.html

## 参考になりそうなもの

- [PicOS Open vSwitch Command Reference](https://docs.pica8.com/display/PICOS2111cg/PicOS+Open+vSwitch+Command+Reference)
  - コマンドのサンプルがいろいろ乗ってます
  - [Creating a Group Table](https://docs.pica8.com/display/picos2102cg/Creating+a+Group+Table)
    - パケットの egress で複数リンクを扱う際にグループ化して冗長化とかするためのやつです
- [OPENSTACK RULES: HOW OPENVSWITCH WORKS INSIDE OPENSTACK](https://aptira.com/openstack-rules-how-openvswitch-works-inside-openstack/)
  - VM の ARP 解決の参考になりました
- [OpenStack Networking: Open vSwitch and VXLAN introduction](https://www.sidorenko.io/post/2018/11/openstack-networking-open-vswitch-and-vxlan-introduction/)
  - OVS で VXLAN やるサンプルです
  - ちゃんと環境構築のコマンド乗ってて解説もされててとても参考になりました
    - ついでに、mirror port の設定サンプルもあってよかったです
- [ARTHURCHIAO'S BLOG](http://arthurchiao.art/articles/)
  - 使い方というよりは、インターナルの話だが OVS 理解のために読むとよいと思います
  - OVS 以外にもネットワーク関連を扱っていて面白いです
  - [2016-12-31 OVS Deep Dive 0: Overview](http://arthurchiao.art/blog/ovs-deep-dive-0-overview/)
  - [2016-12-31 OVS Deep Dive 1: vswitchd](http://arthurchiao.art/blog/ovs-deep-dive-1-vswitchd/)
  - [2017-01-01 OVS Deep Dive 2: OVSDB](http://arthurchiao.art/blog/ovs-deep-dive-2/)
  - [2017-01-01 OVS Deep Dive 3: Datapath](http://arthurchiao.art/blog/ovs-deep-dive-3-datapath/)
  - [2017-01-07 OVS Deep Dive 4: OVS netdev and Patch Port](http://arthurchiao.art/blog/ovs-deep-dive-4-patch-port/)
  - [2017-03-08 OVS Deep Dive 5: Datapath and TX Offloading](http://arthurchiao.art/blog/ovs-deep-dive-5-datapath-tx-offloading/)
  - [2017-03-08 OVS Deep Dive 6: Internal Port](http://arthurchiao.art/blog/ovs-deep-dive-6-internal-port/)
