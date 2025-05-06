import ipaddress

PRIVATE_ASN_START = 4200000000
PRIVATE_ASN_END = 4294967294

# このリスト順にPRIVATE_ASNを割り当てます
# このリストは追加はしてよいが削除はしてはいけない
ASN_NETWORKS = [
    "192.168.0.0/16",
    "172.16.0.0/12",
    "10.0.0.0/8",
]

ASN_IP_NETWORKS = [ipaddress.ip_network(net) for net in ASN_NETWORKS]

# 検証コード1: ボツ案
# 初めの8ビットをprivate ipのみ扱うことを想定
# privateの ipv4, asnの変換であればこのロジックでよい, prefix 4つ分が限界
# available_range = PRIVATE_ASN_END - PRIVATE_ASN_START
# for i in range(0, 100):
#     if int(ipaddress.ip_address(f"{i}.255.255.255")) > available_range:
#         print(int(ipaddress.ip_address(f"{i}.255.255.255")), str(ipaddress.ip_address(f"{i}.255.255.255")))
#         print(i) // 5
#         break


def assign_inet4(network_name, spec):
    network = spec["ipam"][network_name]
    ip_network = ipaddress.ip_network(network["subnet"])
    if network["kind"] == "l2":
        inet = str(ip_network[network["_next_ip"]]) + "/" + str(ip_network.prefixlen)
    else:
        if ip_network.version == 4:
            inet = str(ip_network[network["_next_ip"]]) + "/32"
        else:
            inet = str(ip_network[network["_next_ip"]]) + "/128"
    network["_next_ip"] += 1
    return inet


def gateway_inet4(network_name, spec):
    network = spec["ipam"][network_name]
    ip_network = ipaddress.ip_network(network["subnet"])
    if network["kind"] != "l2":
        raise Exception("gateway_inet4 is supported by l2")
    inet = str(ip_network[1]) + "/" + str(ip_network.prefixlen)
    return inet


def gateway_ip(network):
    ip_network = ipaddress.ip_network(network)
    inet = str(ip_network[1])
    return inet


def inet_to_ip(inet):
    return inet.split("/")[0]


def ipv4_to_asn(ipv4):
    ip_address = ipaddress.ip_address(ipv4)
    asn = PRIVATE_ASN_START
    for ip_network in ASN_IP_NETWORKS:
        if ip_address in ip_network:
            asn += int(ip_address) - int(ip_network.network_address)
            break
        asn += ip_network.num_addresses
    else:
        raise Exception(f"Invalid ipv4: ipv4={ipv4}")
    if asn > PRIVATE_ASN_END:
        raise Exception(f"asn > PRIVATE_ASN_END: ipv4={ipv4}, asn={asn}, PRIVATE_ASN_END={PRIVATE_ASN_END}")
    return asn


def asn_to_ipv4(asn):
    ipi = asn - PRIVATE_ASN_START
    for ip_network in ASN_IP_NETWORKS:
        if ipi <= ip_network.num_addresses:
            ip = ip_network[ipi]
            return str(ip)
        ipi -= ip_network.num_addresses

    raise Exception(f"Invalid asn: asn={asn}")


def asn_to_sid(asn):
    ipi = int(asn) - PRIVATE_ASN_START
    suffix = '{:08x}'.format(ipi)
    sid = f"fc06:0000:{suffix[:4]}:{suffix[4:]}::1/64"
    ip_interface = ipaddress.ip_interface(sid)
    return ip_interface.exploded


def inet4_to_inet6(inet):
    inets = inet.split("/")
    ip = inets[0]
    ipv6 = "fc00:0000:0000:0000:" + ip.replace(".", ":")
    ip_interface = ipaddress.ip_interface(ipv6 + "/" + str(int(inets[1]) * 2 + 64))
    return ip_interface.exploded
