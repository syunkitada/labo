# MAC OUI (Organizationally Unique Identifier) for generated MAC addresses
# Uses a common virtualization OUI: 00:16:3E (Xen/XenSource)
MAC_OUI = [0x00, 0x16, 0x3E]


def complete(manifest: dict):
    if "nodes" not in manifest["spec"]:
        return

    node_map = {}

    for node in manifest["spec"]["nodes"]:
        if node["kind"] == "container":
            node["_hostname"] = f"{node['name']}.{manifest['namespace']}"
        else:
            node["_hostname"] = (
                f"{node['name'].replace('_', '-')}.{manifest['namespace']}.{manifest['spec']['domain']}"
            )

        node["spec"]["_links"] = []
        node_map[node["name"]] = node

    manifest["_referer"]["_node_map"] = node_map

    _complete_links(manifest, node_map)


def _complete_links(manifest: dict, node_map: dict):
    for node_index, node in enumerate(manifest["spec"]["nodes"]):
        if "links" not in node["spec"]:
            continue

        for link_index, link in enumerate(node["spec"]["links"]):
            if "peer" not in link:
                raise Exception(f"peer is not found in link: {link}")

            peer_node = node_map.get(link["peer"])
            if peer_node is None:
                raise Exception(f"peer node {link['peer']} is not found in node_map")

            _complete_link(node_index, node, peer_node, link_index, link)

            peer_node["spec"]["_links"].append(link)


def _complete_link(node_index: int, node: dict, peer_node, link_index: int, link: dict):
    if "mtu" not in link:
        link["mtu"] = 1500

    if "kind" not in link:
        if node["kind"] == "vm" or peer_node["kind"] == "vm":
            # Use TAP interfaces when VMs are involved
            link["kind"] = "tap"
        elif node["kind"] == "container":
            # Use veth pairs for container-to-container links
            link["kind"] = "veth"
        else:
            raise Exception(f"unexpected node kind: {node['kind']}")

    link["src_name"] = node["name"]
    link["link_name"] = f"{node['name']}_{link_index}_{link['peer']}"
    link["peer_name"] = f"{link['peer']}_{link_index}_{node['name']}"

    # Generate MAC addresses if not provided
    # Format: MAC_OUI + [node_index, link_index, 0/1]
    # The last byte (0/1) distinguishes between link and peer sides
    if "link_mac" not in link:
        link["link_mac"] = ":".join(
            map(lambda x: "%02x" % x, MAC_OUI + [node_index, link_index, 0])
        )
    if "peer_mac" not in link:
        link["peer_mac"] = ":".join(
            map(lambda x: "%02x" % x, MAC_OUI + [node_index, link_index, 1])
        )
