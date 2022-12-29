# OVS (Open vSwitch)

## ヘルプ・ドキュメント類

- 公式ドキュメント
  - https://docs.openvswitch.org/en/latest/
- ovs-vsctl
  - ブリッジ構成の確認・操作をするための CLI です
  - http://www.openvswitch.org/support/dist-docs/ovs-vsctl.8.html
  - $ ovs-vsctl -h
- ovs-ofctl
  - ブリッジの openflow の確認・操作をするための CLI です
  - http://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.html
  - $ ovs-ofctl -h
- ovs-appctl
  - Open vSwitch に対していろいろクエリを発行するための CLI です
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

- [OPENSTACK RULES: HOW OPENVSWITCH WORKS INSIDE OPENSTACK](https://aptira.com/openstack-rules-how-openvswitch-works-inside-openstack/)
- [PicOS Open vSwitch Command Reference](https://docs.pica8.com/display/PICOS2111cg/PicOS+Open+vSwitch+Command+Reference)
  - [Creating a Group Table](https://docs.pica8.com/display/picos2102cg/Creating+a+Group+Table)
