import ipaddress

from fabfile.lib.spec_utils import ipam


def test_ipv4_asn():
    ip_network = ipaddress.ip_network(ipam.ASN_NETWORKS[0])
    start_ip = str(ip_network[0])
    start_asn = ipam.ipv4_to_asn(start_ip)
    start_ipv4 = ipam.asn_to_ipv4(start_asn)
    assert start_ip == start_ipv4
    assert start_asn <= ipam.PRIVATE_ASN_END
    assert start_asn >= ipam.PRIVATE_ASN_START

    ip_network = ipaddress.ip_network(ipam.ASN_NETWORKS[-1])
    end_ip = str(ip_network[-1])
    end_asn = ipam.ipv4_to_asn(end_ip)
    end_ipv4 = ipam.asn_to_ipv4(end_asn)
    assert end_ip == end_ipv4
    assert end_asn <= ipam.PRIVATE_ASN_END
    assert end_asn >= ipam.PRIVATE_ASN_START
