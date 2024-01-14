import os


def make(rc):
    spec = rc.spec
    rspec = rc.rspec

    ovs = rspec["ovs"]
    cmds = [
        "systemctl start openvswitch",
    ]

    for bridge in ovs["bridges"]:
        br_name = bridge["name"]
        br_kind = bridge.get("kind", "")
        br_flows = []
        cmds += [
            f"ovs-vsctl --may-exist add-br {br_name}",
            # f"ovs-vsctl set bridge {br_name} datapath_type=netdev protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13,OpenFlow14,OpenFlow15",
            f"ip link set up {br_name}",
        ]
        if br_kind == "external-ha":
            for i, ex_ip in enumerate(ovs.get("admin_ips", [])):
                rc.append_cmds_ip_addr_add(cmds, ex_ip, br_name)
                table = f"20{i}"
                iprule = f"from {ex_ip['ip']} table {table}"
                cmds += rc.wrap_if_exist_iprule(iprule, [
                    f"ip rule add {iprule} prio 25",
                ])
                cmds += [
                    f"ip route replace table {table} 0.0.0.0/0 dev {br_name} src {ex_ip['ip']}",
                ]

            for link in rspec["_links"]:
                for vlan_id, vlan in link["vlan_map"].items():
                    peer_ovs = vlan.get("peer_ovs")
                    if peer_ovs is not None and peer_ovs["peer"] == br_name:
                        cmds += [f"ovs-vsctl --may-exist add-port {br_name} {link['peer_name']}.{vlan_id}"]
                        link_name = f"{br_name}-{peer_ovs['peer_name']}"
                        cmds += rc.wrap_if_exist_netdev(peer_ovs["peer_name"], [
                            f"ip link add {link_name} type veth peer name {peer_ovs['peer_name']}",
                            f"ip link set dev {link_name} mtu {link['mtu']}",
                            f"ip link set {link_name} up",
                            f"ethtool -K {link_name} tso off tx off",
                            f"ip link set dev {peer_ovs['peer_name']} up",
                            f"ethtool -K {peer_ovs['peer_name']} tso off tx off",
                        ])
                        cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {link_name}"]

            group1_ports = []
            for link in rspec["_links"]:
                for vlan_id, vlan in link["vlan_map"].items():
                    peer_ovs = vlan.get("peer_ovs")
                    if peer_ovs is not None and peer_ovs["peer"] == br_name:
                        ex_peer_name = f"{link['peer_name']}.{vlan_id}"
                        bgp_link_name = f"{br_name}-{peer_ovs['peer_name']}"
                        br_flows += [
                            # linklocalのbgp用の通信のingress
                            f"priority=800,ipv6,in_port={ex_peer_name},ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:{bgp_link_name}",
                            f"priority=800,ipv6,in_port={ex_peer_name},ipv6_dst=ff02::/16 actions=output:{bgp_link_name}",
                            # linklocalのbgp用の通信のegress
                            f"priority=800,ipv6,in_port={bgp_link_name},ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:{ex_peer_name}",
                            f"priority=800,ipv6,in_port={bgp_link_name},ipv6_dst=ff02::/16 actions=output:{ex_peer_name}",
                        ]
                        group1_ports += [f"bucket=watch_port:{ex_peer_name},actions=mod_dl_dst:{link['link_mac']},output:{ex_peer_name}"]

                        for link in bridge.get("links", []):
                            for flow in link.get("flows", []):
                                if flow["kind"] == "ingress":
                                    br_flows += [
                                        f"priority=700,ip,in_port={ex_peer_name} actions=output:{link['link_name']}",
                                    ]

            # bridgeのmacは、一つ目のinterfaceのmacと一緒になる(厳密にはbridgeからちゃんとmacを取得したほうが良い)
            bridge_mac = rspec["_links"][0]["peer_mac"]
            for ex_ip in ovs.get("admin_ips", []):
                br_flows += [
                    # ingress
                    f"priority=750,ip,nw_dst={ex_ip['ip']} actions=mod_dl_dst:{bridge_mac},output:LOCAL",
                    # egress
                    f"priority=750,ip,in_port=LOCAL,nw_src={ex_ip['ip']} actions=group:1",
                ]

            for link in bridge.get("links", []):
                for flow in link.get("flows", []):
                    if flow["kind"] == "egress":
                        br_flows += [
                            f"priority=700,ip,in_port={link['link_name']} actions=group:1",
                        ]

            buckets = ",".join(group1_ports)
            # egressの通信を冗長化させる
            cmds += [
                f'ovs-ofctl -O OpenFlow15 mod-group --may-create {br_name} "group_id=1,type=select,selection_method=hash,fields(ip_src,ip_dst),'
                + buckets
                + '"'
            ]

            _append_flows_for_dummy_arp(br_flows, "LOCAL")

        elif br_kind == "internal-vm":
            for child_link in rspec.get("child_links", []):
                cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {child_link['link_name']}"]
                child_link_mac = f"0x{child_link['peer_mac'].replace(':', '')}"
                for ip in child_link.get("peer_ips", []):
                    for _link in bridge.get("_links", []):
                        br_flows += [
                            # ingress
                            # 宛先のmacをvmのmacに書き換える(VMにはL2通信してるように思わせる)
                            f"priority=700,ip,in_port={_link['peer_name']},nw_dst={ip['ip']}"
                            + f" actions=mod_dl_dst:{child_link['peer_mac']},output:{child_link['link_name']}",
                            # egress
                            f"priority=700,ip,in_port={child_link['link_name']},nw_src={ip['ip']} actions=output:{_link['peer_name']}",
                        ]

                        _append_flows_for_dummy_arp(br_flows, child_link["link_name"])

        elif br_kind == "vxlan-vpc-vm":
            vxlan_eth = f"vxlan{bridge['vpc_id']}"
            tun_src = ""
            for ip in ovs.get("admin_ips", []):
                tun_src = ip["ip"]
            vxlan_options = f" options:local_ip={tun_src}"
            cmds += [
                f"ovs-vsctl --may-exist add-port {br_name} {vxlan_eth} --"
                f" set interface {vxlan_eth} type=vxlan options:remote_ip=flow options:key={bridge['vpc_id']}{vxlan_options}"
            ]
            for child_link in rspec.get("child_links", []):
                if bridge["vpc_id"] != child_link["vpc_id"]:
                    continue
                cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {child_link['link_name']}"]
                child_link_mac = f"0x{child_link['peer_mac'].replace(':', '')}"
                for ip in child_link.get("peer_ips", []):
                    br_flows += [
                        # ingress
                        # 宛先のmacをvmのmacに書き換える(VMにはL2通信してるように思わせる)
                        f"priority=700,ip,,nw_dst={ip['ip']}"
                        + f" actions=load:{child_link_mac}->NXM_OF_ETH_DST[],output:{child_link['link_name']}",
                    ]

                    _append_flows_for_dummy_arp(br_flows, child_link["link_name"])

                # 同一vpc間通信はHV to HVでフルメッシュのリンクにする
                # disableの場合はGW経由での通信となる
                if not bridge.get("disable_vpc_fullmesh", False):
                    for ex_vtep in bridge["ex_vteps"]:
                        for _link in ex_vtep["dst"]["_links"]:
                            for ip in _link["peer_ips"]:
                                br_flows += [
                                    f"priority=700,ip,nw_dst={ip['ip']} actions=set_field:{ex_vtep['tun_dst']}->tun_dst,{vxlan_eth}",
                                ]
            for vip in spec.get("vip_map", {}).values():
                if vip["vpc_id"] == bridge["vpc_id"]:
                    br_flows += [
                        # FIXME
                        # f"priority=700,ip,nw_dst={vip['vip']['ip']} actions=set_field:{vip['tun_vip']['ip']}->tun_dst,{vxlan_eth}",
                    ]

            # 行先不明ならGWへ
            if "_vpcgw" in bridge:
                br_flows += [
                    f"priority=600 actions=set_field:{bridge['_vpcgw']['vtep']['ip']}->tun_dst,{vxlan_eth}",
                ]

        elif br_kind == "vxlan-vpc-vpcgw":
            vxlan_options = ""
            if "ex_ip" in ovs:
                vxlan_options = f" options:local_ip={ovs['ex_ip']['ip']}"
            cmds += [
                f"ovs-vsctl --may-exist add-port {br_name} vxlan --"
                f" set interface vxlan type=vxlan options:remote_ip=flow options:key=flow{vxlan_options}"
            ]

            egress_link = None
            for link in bridge.get("links", []):
                for flow in link.get("flows", []):
                    if egress_link is None and flow["kind"] == "egress":
                        egress_link = link

            # eip宛て通信
            #    - 同一clusterへ
            #    - 別clusterへ(TODO)
            # 同一vpc宛て通信
            #    - 同一cluster配下へ
            #    - 別clusterへ(TODO)
            # nonvpc宛て通信
            vpcgw = rspec["_vpcgw"]
            for tun_id, tlinks in vpcgw["_vpc_links_map"].items():
                for tlink in tlinks:
                    br_flows += [
                        # ingress to same vpc in same cluster
                        # メモ: IN_PORT ではなくoutput:vxlanとすると処理されないので注意
                        f"priority=800,in_port=vxlan,tun_id={tun_id},ip,nw_dst={tlink['ip']} "
                        + f"actions=set_field:{tun_id}->tun_id,set_field:{tlink['tun_dst']}->tun_dst,IN_PORT",
                    ]
                    for link in bridge.get("links", []):
                        for flow in link.get("flows", []):
                            if flow["kind"] == "ingress":
                                br_flows += [
                                    # ingress to eip
                                    # snat vpcip to eip
                                    f"priority=700,in_port=vxlan,tun_id={tun_id},ip,nw_src={tlink['ip']} "
                                    + f"actions=set_field:{tlink['eip']}->nw_src,output:{link['link_name']}",
                                ]
                    if egress_link is not None:
                        br_flows += [
                            # egress
                            # dnat eip to ip
                            f"priority=700,in_port={egress_link['link_name']},ip,nw_dst={tlink['eip']} "
                            + f"actions=set_field:{tlink['ip']}->nw_dst,set_field:{tun_id}->tun_id,set_field:{tlink['tun_dst']}->tun_dst,vxlan",
                        ]

        elif br_kind == "vxlan-vpc-lb":
            # これは疑似的なVPCテナント用のLBです（ちゃんとLBするわけではない）
            vxlan_eth = f"vxlan{bridge['vpc_id']}"
            tun_src = ""
            for ip in ovs.get("admin_ips", []):
                tun_src = ip["ip"]
            vxlan_options = f" options:local_ip={tun_src}"
            cmds += [
                f"ovs-vsctl --may-exist add-port {br_name} {vxlan_eth} --"
                f" set interface {vxlan_eth} type=vxlan options:remote_ip=flow options:key={bridge['vpc_id']}{vxlan_options}"
            ]
            for vip in spec["vip_map"].values():
                if vip["vpc_id"] != bridge["vpc_id"]:
                    continue
                for member in vip["members"]:
                    # FIXME
                    continue
                    tun_dst = member["_node"]["hv"]["ovs"]["admin_ips"][0]
                    for link in member["_node"]["_links"]:
                        for ip in link["peer_ips"]:
                            # FIXME
                            br_flows += [
                                f"priority=700,in_port={vxlan_eth},ip actions=set_field:{ip['ip']}->nw_dst,set_field:{tun_dst}->tun_dst,IN_PORT",
                            ]
            # for child_link in rspec.get("child_links", []):
            #     if bridge["vpc_id"] != child_link["vpc_id"]:
            #         continue
            #     cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {child_link['link_name']}"]
            #     child_link_mac = f"0x{child_link['peer_mac'].replace(':', '')}"
            #     for ip in child_link.get("peer_ips", []):
            #         br_flows += [
            #             # ingress
            #             # 宛先のmacをvmのmacに書き換える(VMにはL2通信してるように思わせる)
            #             f"priority=700,ip,,nw_dst={ip['ip']}"
            #             + f" actions=load:{child_link_mac}->NXM_OF_ETH_DST[],output:{child_link['link_name']}",
            #         ]

            #         _append_flows_for_dummy_arp(br_flows, child_link["link_name"])

            #     # 同一vpc間通信はHV to HVでフルメッシュのリンクにする
            #     # disableの場合はGW経由での通信となる
            #     if not bridge.get("disable_vpc_fullmesh", False):
            #         for ex_vtep in bridge["ex_vteps"]:
            #             for _link in ex_vtep["dst"]["_links"]:
            #                 for ip in _link["peer_ips"]:
            #                     br_flows += [
            #                         f"priority=700,ip,nw_dst={ip['ip']} actions=set_field:{ex_vtep['tun_dst']}->tun_dst,{vxlan_eth}",
            #                     ]

        elif br_kind == "aclgw":
            for link in bridge.get("links", []):
                for flow in link.get("flows", []):
                    if flow["kind"] == "ingress":
                        if flow.get("match_kind", "") == "vpc-eip":
                            vpcgw = rspec["_vpcgw"]
                            for _, tlinks in vpcgw["_vpc_links_map"].items():
                                for tlink in tlinks:
                                    br_flows += [
                                        f"priority=700,ip,nw_dst={tlink['eip']} actions=output:{link['link_name']}",
                                    ]
                        else:
                            br_flows += [
                                f"priority=600,ip actions=output:{link['link_name']}",
                            ]

        else:
            ingress_link = None
            egress_link = None
            for link in bridge.get("_links", []):
                for flow in link.get("flows", []):
                    if ingress_link is None and flow["kind"] == "ingress":
                        ingress_link = link
                    elif egress_link is None and flow["kind"] == "egress":
                        egress_link = link
            if ingress_link is not None and egress_link is not None:
                br_flows += [
                    f"priority=700,in_port={ingress_link['peer_name']} actions=output:{egress_link['peer_name']}",
                ]

        cmds += [f"# {br_name} {br_kind}"]
        for link in bridge.get("links", []):
            if link.get("kind", "") != "local":
                cmds += [
                    f"ovs-vsctl --may-exist add-port {br_name} {link['link_name']}"
                    + f" -- set interface {link['link_name']} type=patch options:peer={link['peer_name']}"
                ]
        for link in bridge.get("_links", []):
            cmds += [
                f"ovs-vsctl --may-exist add-port {br_name} {link['peer_name']}"
                + f" -- set interface {link['peer_name']} type=patch options:peer={link['link_name']}"
            ]

        if len(br_flows) > 0:
            br_flows += [
                "priority=0,actions=drop",
            ]
            flows_filepath = os.path.join(rspec["_script_dir"], f"{br_name}.flows")
            with open(flows_filepath, "w") as f:
                f.write("\n".join(br_flows))
            cmds += [f"ovs-ofctl -O OpenFlow15 replace-flows {br_name} {flows_filepath}"]

    rc.exec(cmds, title="ovs")


ARP_DUMMY_MAC = "0x00163e000001"


def _append_flows_for_dummy_arp(br_flows, in_port=None):
    # in_portからARP要求(arp_op=1)が飛んできたときに、ARP_DUMMY_MACを返却します
    # arp_op = NXM_OF_ARP_OP = Opcode of ARP, リクエストは1、リプライは2 をセットします
    # NXM_OF_ETH_SRC = Ethernet Source address
    # NXM_OF_ETH_DST = Ethernet Destination address
    # NXM_NX_ARP_SHA = ARP Source Hardware(Ethernet) Address
    # NXM_NX_ARP_THA = ARP Target Hardware(Ethernet) Address
    # NXM_OF_ARP_SPA = ARP Source IP Address
    # NXM_OF_ARP_TPA = ARP Target IP Address
    in_port_option = ""
    if in_port is not None:
        in_port_option = f",in_port={in_port}"
    br_flows += [
        f"priority=800{in_port_option},arp,arp_op=1 actions="
        # NXM_OF_ETH_SRCをNXM_OF_ETH_DSTにセットして、ARP_DUMMY_MACをNXM_OF_ETH_SRCにセットする
        + f"move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[],load:{ARP_DUMMY_MAC}->NXM_OF_ETH_SRC[],"
        # NXM_NX_ARP_SHAをNXM_NX_ARP_THAにセットして、ARP_DUMMY_MACをNXM_NX_ARP_SHAにセットする
        + f"move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[],load:{ARP_DUMMY_MAC}->NXM_NX_ARP_SHA[],"
        # NXM_OF_ARP_SPAとNXM_OF_ARP_TPAを入れ替える
        + "push:NXM_OF_ARP_TPA[],move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[],pop:NXM_OF_ARP_SPA[],"
        # Opcodeを2にセットする(ARPのリプライであることを示すフラグ)
        + "load:0x2->NXM_OF_ARP_OP[],"
        # IN_PORTにそのまま返す
        + "IN_PORT"
    ]


def check():
    pass
    # ovs-appctl ofproto/trace br-ex in_port=GW1_2_L12.200,icmp,nw_dst=10.110.0.1
    # ovs-vxlan5-HV1 ovs-appctl ofproto/trace br-t1 in_port=HV1_0_t1vm1,icmp,nw_dst=10.100.0.3
