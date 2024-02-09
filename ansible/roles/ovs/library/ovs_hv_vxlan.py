#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ovs_hv_vxlan

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import time
import os


def run_module():
    def run(*args, **kwargs):
        result = subprocess.run(*args, **kwargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result.stdout = result.stdout.decode('utf-8')
        return result


    def must_run(*args, retry=0, interval=1, **kwargs):
        result = run(*args, **kwargs)
        if result.returncode != 0:
            if retry == 0:
                raise Exception("Failed to run: \n"
                    f"return_code={result.check_returncode}\n"
                    f"out={result.stdout}\n"
                    f"err={result.stderr}")
            time.sleep(interval)
            must_run(*args, **kwargs, retry=retry, interval=interval)
        return result

    module_args = dict(
        ovs=dict(type='dict', required=True),
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    ovs = module.params['ovs']

    must_run(["ovs-vsctl", "--may-exist", "add-br", ovs['external_bridge']['name']])
    must_run(["ip", "link", "set", "up", ovs['external_bridge']['name']])
    cmd_result = must_run(["ip", "addr", "show", "dev", ovs['external_bridge']['name']])
    if f"inet {ovs['external_bridge']['local_ip']}/32" not in cmd_result.stdout:
        must_run(["ip", "addr", "add", f"{ovs['external_bridge']['local_ip']}/32", "dev", "br-ex"])

    cmd_result = must_run(["ip", "rule"])
    if f"from {ovs['external_bridge']['local_ip']} table 200" not in cmd_result.stdout.replace('lookup', 'table'):
        must_run(["ip", "rule", "add", "from", ovs['external_bridge']['local_ip'], "table", "200", "prio", "25"])
    must_run(["ip", "route", "replace", "table", "200", "0.0.0.0/0", "dev", "br-ex", "src", ovs['external_bridge']['local_ip']])

    br_flows = []
    buckets = []
    for i, interface in enumerate(ovs['external_bridge']['interfaces']):
        must_run(["ovs-vsctl", "--may-exist", "add-port", ovs['external_bridge']['name'], interface['name']])
        bgp_interface = f"bgp{i}"
        interface_name = f"{ovs['external_bridge']['name']}-{bgp_interface}"

        br_flows += [
            # linklocalのbgp用の通信のingress
            f"priority=800,ipv6,in_port={interface['name']},ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:{interface_name}",
            f"priority=800,ipv6,in_port={interface['name']},ipv6_dst=ff02::/16 actions=output:{interface_name}",
            # linklocalのbgp用の通信のegress
            f"priority=800,ipv6,in_port={interface_name},ipv6_src=fe80::/10,ipv6_dst=fe80::/10 actions=output:{interface['name']}",
            f"priority=800,ipv6,in_port={interface_name},ipv6_dst=ff02::/16 actions=output:{interface['name']}",
        ]

        if run(['ip', 'addr', 'show', 'dev', bgp_interface]).returncode != 0:
            must_run(["ip", "link", "add", interface_name,
                "type", "veth", "peer", "name", bgp_interface])
            must_run(['ip', 'link', 'set', 'dev', interface_name, 'mtu', '9000'])
            must_run(['ip', 'link', 'set', interface_name, 'up'])
            must_run(['ethtool', '-K', interface_name, 'tso', 'off', 'tx', 'off'])
            must_run(['ip', 'link', 'set', 'dev', bgp_interface, 'up'])
            must_run(['ethtool', '-K ', bgp_interface, 'tso', 'off', 'tx', 'off'])
        must_run(['ovs-vsctl', '--no-wait', '--may-exist', 'add-port', ovs['external_bridge']['name'], interface_name])

        buckets.append(f"bucket=watch_port:{interface['name']},actions=mod_dl_dst:{interface['peer_mac']},output:{interface['name']}")

    must_run(['ovs-ofctl', '-O', 'OpenFlow15', 'mod-group', '--may-create', ovs['external_bridge']['name'],
      f'group_id=1,type=select,selection_method=hash,fields(ip_src,ip_dst),{",".join(buckets)}'])

    _append_flows_for_dummy_arp(br_flows, "LOCAL")

    cmd_result = must_run(["ip", "link", "show", "br-ex"])
    bridge_mac = cmd_result.stdout.split("link/ether ")[1].split(" ")[0]
    br_flows += [
        f"priority=750,ip,nw_dst={ovs['external_bridge']['local_ip']} actions=mod_dl_dst:{bridge_mac},LOCAL",
        f"priority=750,ip,in_port=LOCAL,nw_src={ovs['external_bridge']['local_ip']} actions=group:1",
    ]

    if len(br_flows) > 0:
        br_flows += [
            "priority=0,actions=drop",
        ]
        flows_filepath = f"/tmp/{ovs['external_bridge']['name']}.flows"
        with open(flows_filepath, "w") as f:
            f.write("\n".join(br_flows))
        must_run(["ovs-ofctl", "-O", "OpenFlow15", "replace-flows", ovs['external_bridge']['name'], flows_filepath])

    # external-bridge

    for bridge in ovs.get("vxlan_bridges", []):
        must_run(["ovs-vsctl", "--may-exist", "add-br", bridge["name"]])

        br_flows = []
        vxlan_eth = f"vxlan{bridge['vxlan_id']}"
        vxlan_options = f" options:local_ip={ovs['external_bridge']['local_ip']}"
        must_run([
            "ovs-vsctl", "--may-exist", "add-port", bridge['name'], vxlan_eth, "--",
            "set", "interface", vxlan_eth, "type=vxlan", "options:remote_ip=flow", f"options:key={bridge['vxlan_id']}{vxlan_options}",
        ])

        for port in bridge['ports']:
            must_run(["ovs-vsctl", "--no-wait", "--may-exist", "add-port", bridge['name'], port['name']])
            port_peer_mac = f"0x{port['peer_mac'].replace(':', '')}"
            for ip in port.get("ips", []):
                br_flows += [
                    # ingress
                    # 宛先のmacをvmのmacに書き換える(VMにはL2通信してるように思わせる)
                    f"priority=800,ip,nw_dst={ip}"
                    f" actions=load:{port_peer_mac}->NXM_OF_ETH_DST[],output:{port['name']}",
                ]

                _append_flows_for_dummy_arp(br_flows, port["name"])

        for route in bridge.get('routes', []):
            br_flows += [
                f"priority=700,ip,nw_dst={route['ip']} actions=set_field:{route['dst']}->tun_dst,{vxlan_eth}",
            ]

        if len(br_flows) > 0:
            br_flows += [
                "priority=0,actions=drop",
            ]
            flows_filepath = f"/tmp/{bridge['name']}.flows"
            with open(flows_filepath, "w") as f:
                f.write("\n".join(br_flows))
            must_run(["ovs-ofctl", "-O", "OpenFlow15", "replace-flows", bridge['name'], flows_filepath])


    result['message'] = 'success'
    result['changed'] = True

    module.exit_json(**result)


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



def main():
    run_module()


if __name__ == '__main__':
    main()
