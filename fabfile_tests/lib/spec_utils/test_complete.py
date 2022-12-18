from fabfile.lib.spec_utils import complete


def test_complete_spec():
    spec = {
        "ipam": {
            "network1": {
                "kind": "l2",
                "subnet": "10.10.0.0/24",
            },
            "network2": {
                "kind": "l3",
                "subnet": "10.10.1.0/24",
            },
        },
        "common": {
            "namespace": "test",
            "nfs_path": "/mnt/nfs",
        },
        "template_map": {
            "node1": {
                "kind": "container",
            },
        },
        "nodes": [
            {
                "name": "node1",
                "templates": ["node1"],
                "links": [
                    {
                        "peer": "node2",
                        "ips": [
                            {"inet": "${assign_inet4(network1)}"},
                            {"inet": "${inet4_to_inet6(links.0.ips.0.inet)}"},
                        ],
                    },
                ],
            },
            {
                "name": "node2",
                "templates": ["node1"],
                "lo_ips": [
                    {"inet": "${assign_inet4(network2)}"},
                ],
                "frr": {
                    "id": "${lo_ips.0.ip}",
                    "asn": "${ipv4_to_asn(lo_ips.0.ip)}",
                    "ipv4_networks": [
                        "${_node_map.node1.links.0.ips.0.network}",
                    ],
                    "ipv6_networks": [
                        "${_node_map.node1.links.0.ips.1.network}",
                    ],
                    "route_maps": [
                        {
                            "prefix_list": [
                                "permit ${ipam.network1.subnet} le 32",
                            ],
                        },
                    ],
                },
            },
        ],
    }

    completed_spec = {
        "nodes": [
            {
                "name": "node1",
                "templates": ["node1"],
                "kind": "container",
                "links": [
                    {
                        "ips": [
                            {"inet": "10.10.0.2/24", "ip": "10.10.0.2", "network": "10.10.0.0/24", "version": "4"},
                            {
                                "inet": "fc00:0000:0000:0000:10:10:0:2/112",
                                "ip": "fc00::10:10:0:2",
                                "network": "fc00::10:10:0:0/112",
                                "version": "6",
                            },
                        ],
                        "link_mac": "00:16:3e:00:00:00",
                        "link_name": "node1_0_node2",
                        "peer": "node2",
                        "peer_mac": "00:16:3e:00:00:01",
                        "peer_name": "node2_0_node1",
                        "src_name": "node1",
                    }
                ],
                "_hostname": "test-node1",
                "_script_index": 0,
                "_script_dir": "/mnt/nfs/labo_nodes/test-node1",
                "_links": [],
            },
            {
                "name": "node2",
                "templates": ["node1"],
                "kind": "container",
                "lo_ips": [
                    {"inet": "10.10.1.1/32", "ip": "10.10.1.1", "network": "10.10.1.1/32", "version": "4"},
                ],
                "frr": {
                    "id": "10.10.1.1",
                    "asn": "4201769729",
                    "ipv4_networks": ["10.10.0.0/24"],
                    "ipv6_networks": ["fc00::10:10:0:0/112"],
                    "route_maps": [
                        {
                            "prefix_list": [
                                "permit 10.10.0.0/24 le 32",
                            ],
                        },
                    ],
                },
                "_hostname": "test-node2",
                "_script_index": 0,
                "_script_dir": "/mnt/nfs/labo_nodes/test-node2",
                "_links": [],
            },
        ],
    }
    completed_spec["nodes"][1]["_links"].append(completed_spec["nodes"][0]["links"][0])
    complete.complete_spec(spec)
    assert spec["nodes"] == completed_spec["nodes"]
