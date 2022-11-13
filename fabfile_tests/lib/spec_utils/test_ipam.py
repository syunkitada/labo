from fabfile.lib.spec_utils import ipam


def test_ipv4_asn():
    start_ip = f"{ipam.ASN_IP_PREFIX[0]}.0.0.0"
    start_asn = ipam.ipv4_to_asn(start_ip)
    start_ipv4 = ipam.asn_to_ipv4(start_asn)
    assert start_ip == start_ipv4
    assert start_asn <= ipam.PRIVATE_ASN_END
    assert start_asn >= ipam.PRIVATE_ASN_START

    end_ip = f"{ipam.ASN_IP_PREFIX[-1]}.255.255.255"
    end_asn = ipam.ipv4_to_asn(end_ip)
    end_ipv4 = ipam.asn_to_ipv4(end_asn)
    assert end_ip == end_ipv4
    assert end_asn <= ipam.PRIVATE_ASN_END
    assert end_asn >= ipam.PRIVATE_ASN_START
