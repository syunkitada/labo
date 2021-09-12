# network1

## IP 割り当て

- グローバル IP 10.0.0.0/8
- プライベート IP 192.168.0.0/16

## AS 割り当て

- グローバル AS 65100 - 65399
- プライベート AS 65400 - 65500

```
# seg : bridge : peer node(ip:as)
tier1(10.1.0.0/24)     : tier1-br : tier11(10.1.0.11:65100) <-> tier12(10.1.0.12:65200) <-> tier13(10.1.0.13:65300)
                         tier1-br <-> tier1-br-veth1 <-> tier11-veth <-> tier11
                         tier1-br <-> tier1-br-veth2 <-> tier12-veth <-> tier12
                         tier1-br <-> tier1-br-veth3 <-> tier13-veth <-> tier13

tier11(10.110.0.0/24) : tier11-br : tier11(10.110.0.10:65100) <-> tier111(10.110.0.11:65110)
                                    tier11(10.110.0.10:65100) <-> tier112(10.110.0.12:65120)
                        tier11-br <-> tier11-br-veth0 <-> tier110-veth <-> tier11
                        tier11-br <-> tier11-br-veth1 <-> tier111-veth <-> tier111
                        tier11-br <-> tier11-br-veth2 <-> tier112-veth <-> tier112

tier12(10.120.0.0/24) : tier12-br : tier12(10.120.0.10:65200) <-> tier121(10.120.0.11:65210)
                                    tier12(10.120.0.10:65200) <-> tier122(10.120.0.12:65220)
                        tier12-br <-> tier12-br-veth0 <-> tier120-veth <-> tier120
                        tier12-br <-> tier12-br-veth1 <-> tier121-veth <-> tier121
                        tier12-br <-> tier12-br-veth2 <-> tier122-veth <-> tier122


tier111(10.111.0.0/24) : tier111-br : tier111(10.111.0.10:65110) <-> as1111(10.111.0.11:65111)
                                      tier111(10.111.0.10:65110) <-> as1112(10.111.0.12:65112)
                         tier111-br <-> tier111-br-veth0 <-> tier1110-veth <-> tier111
                         tier111-br <-> tier111-br-veth1 <-> tier1111-veth <-> as1111
                         tier111-br <-> tier111-br-veth2 <-> tier1112-veth <-> as1112

tier121(10.121.0.0/24) : tier111-br : tier121(10.121.0.11:65210) <-> as1211(10.121.0.11:65211)

as1111(10.111.1.0/24) : border-router(10.111.1.1)
  - seg: 10.111.1.16/28
    - as1111-16-br : as1111(10.111.1.17) <-> as1111-16-server1(10.111.1.21)
      as1111-16-br <-> as1111-16-br-veth0 <-> as1111-16-as1111-veth <-> as1111
      as1111-16-br <-> as1111-16-br-veth1 <-> as1111-16-server1-veth <-> as1111-16-server1

  - seg: 10.111.1.32/28
  - core-router1
    - core-switch11
      - lb1 (10.111.1.11, 10.111.1.12, ..)
      - tor-ex1:
        - server11 : 10.111.1.31
        - server12 : 10.111.1.32
      - tor1:
        - server11 : 192.168.1.1
        - server12 : 192.168.1.2
      - tor2:
        - server11 : 192.168.2.1
        - server12 : 192.168.2.2
      - ...

    - core-switch12
      - ...

  - core-router2
    - core-switch21
      - ...
    - core-switch22
      - ...


as1112(10.111.2.0/24) : border-router(10.111.2.1)
  - client11121(10.111.2.11)
  - ...


as1211(10.121.1.0/24) : border-router(10.121.2.1)
  - client12111(10.121.2.11)
  - ...

```
