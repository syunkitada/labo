import os


def make(rc):
    rspec = rc.rspec

    ovs = rspec["ovs"]
    cmds = [
        "systemctl start openvswitch",
    ]

    for bridge in ovs["bridges"]:
        br_name = bridge["name"]
        br_flows = []
        cmds += [
            f"ovs-vsctl --may-exist add-br {br_name}",
            f"ovs-vsctl set bridge {br_name} datapath_type=netdev protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13,OpenFlow14,OpenFlow15",
            f"ip link set up {br_name}",
        ]
        if bridge["kind"] == "external-ha":
            for link in rspec["_links"]:
                for vlan_id, vlan in link["vlan_map"].items():
                    peer_ovs = vlan.get("peer_ovs")
                    if peer_ovs is not None and peer_ovs["peer"] == br_name:
                        cmds += [f"ovs-vsctl --may-exist add-port {br_name} {link['peer_name']}.{vlan_id}"]
                        dryrun = rc.exist_netdev(peer_ovs["peer_name"])
                        link_name = f"{br_name}-{peer_ovs['peer_name']}"
                        cmds += [
                            (f"ip link add {link_name} type veth peer name {peer_ovs['peer_name']}", dryrun),
                            (f"ip link set dev {link_name} mtu {link['mtu']}", dryrun),
                            (f"ip link set {link_name} up", dryrun),
                            (f"ethtool -K {link_name} tso off tx off", dryrun),
                            (f"ip link set dev {peer_ovs['peer_name']} up", dryrun),
                            (f"ethtool -K {peer_ovs['peer_name']} tso off tx off", dryrun),
                        ]
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
                                elif flow["kind"] == "egress":
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

        elif bridge["kind"] == "internal-vm":
            for vm_link in rspec["vm_links"]:
                cmds += [f"ovs-vsctl --no-wait --may-exist add-port {br_name} {vm_link['link_name']}"]
                vm_link_mac = f"0x{vm_link['peer_mac'].replace(':', '')}"
                for ip in vm_link.get("peer_ips", []):
                    for _link in bridge.get("_links", []):
                        br_flows += [
                            # ingress
                            # 宛先のmacをvmのmacに書き換える(VMにはL2通信してるように思わせる)
                            f"priority=700,ip,in_port={_link['peer_name']},nw_dst={ip['ip']}"
                            + f" actions=load:{vm_link_mac}->NXM_OF_ETH_DST[],output:{vm_link['link_name']}",
                            # egress
                            f"priority=700,ip,in_port={vm_link['link_name']},nw_src={ip['ip']} actions=output:{_link['peer_name']}",
                        ]

                        # VMのインターフェイスからARP要求(arp_op=1)が飛んできたときに、dummy_macを返却します
                        # arp_op = NXM_OF_ARP_OP = Opcode of ARP, リクエストは1、リプライは2 をセットします
                        # NXM_OF_ETH_SRC = Ethernet Source address
                        # NXM_OF_ETH_DST = Ethernet Destination address
                        # NXM_NX_ARP_SHA = ARP Source Hardware(Ethernet) Address
                        # NXM_NX_ARP_THA = ARP Target Hardware(Ethernet) Address
                        # NXM_OF_ARP_SPA = ARP Source IP Address
                        # NXM_OF_ARP_TPA = ARP Target IP Address
                        dummy_mac = "0x00163e000001"
                        br_flows += [
                            f"priority=800,in_port={vm_link['link_name']},arp,arp_op=1 actions="
                            # NXM_OF_ETH_SRCをNXM_OF_ETH_DSTにセットして、dummy_macをNXM_OF_ETH_SRCにセットする
                            + f"move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[],load:{dummy_mac}->NXM_OF_ETH_SRC[],"
                            # NXM_NX_ARP_SHAをNXM_NX_ARP_THAにセットして、dummy_macをNXM_NX_ARP_SHAにセットする
                            + f"move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[],load:{dummy_mac}->NXM_NX_ARP_SHA[],"
                            # NXM_OF_ARP_SPAとNXM_OF_ARP_TPAを入れ替える
                            + "push:NXM_OF_ARP_TPA[],move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[],pop:NXM_OF_ARP_SPA[],"
                            # Opcodeを2にセットする(ARPのリプライであることを示すフラグ)
                            + "load:0x2->NXM_OF_ARP_OP[],"
                            # IN_PORTにそのまま返す
                            + "IN_PORT"
                        ]

        for link in bridge.get("links", []):
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
