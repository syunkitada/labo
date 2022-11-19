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


def ipv4_to_asn(ipv4):
    ip_address = ipaddress.ip_address(ipv4)
    asn = PRIVATE_ASN_START
    for ip_network in ASN_IP_NETWORKS:
        if ip_address in ip_network:
            print(ip_address, ip_network.network_address)
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


def ipv4_to_ipv6():
    return 111


def ipv4_to_srv6sid():
    return 111


asn = ipv4_to_asn("10.255.255.255")
print(asn)
ip = asn_to_ipv4(asn)
print(ip)
