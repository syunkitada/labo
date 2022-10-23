# router utils

import ipaddress


def make_gw(c, spec):
    # setup bridge
    br = c.sudo(f"ip addr show '{spec['name']}'", hide=True, warn=True)
    if br.failed:
        c.sudo(f"ip link add {spec['name']} type bridge")

    if spec["ip"] not in br.stdout:
        c.sudo(f"ip addr add dev '{spec['name']}' {spec['ip']}")
        c.sudo(f"ip link set '{spec['name']}' up")

    ip = ipaddress.ip_interface(spec["ip"])

    # setup iptables for NAT
    masqueradeTcpMap = {}
    masqueradeUdpMap = {}
    returnMap = {}
    natTable = c.sudo("iptables -t nat -L", hide=True).stdout
    for line in natTable.splitlines():
        columns = line.split()
        if len(columns) < 3:
            continue
        if columns[0] == "MASQUERADE":
            if columns[1] == "tcp":
                masqueradeTcpMap[columns[3]] = True
            elif columns[1] == "udp":
                masqueradeUdpMap[columns[3]] = True
        elif columns[0] == "RETURN":
            returnMap[columns[3]] = True

    if masqueradeTcpMap.get(ip.network) is None:
        c.sudo(f"iptables -t nat -A POSTROUTING -p TCP -s {spec['ip']} ! -d {spec['ip']} -j MASQUERADE --to-ports 30000-40000")
    if masqueradeUdpMap.get(ip.network) is None:
        c.sudo(f"iptables -t nat -A POSTROUTING -p UDP -s {spec['ip']} ! -d {spec['ip']} -j MASQUERADE --to-ports 30000-40000")
    if returnMap.get(ip.network) is None:
        c.sudo(f"iptables -t nat -A POSTROUTING -s {spec['ip']} -d 255.255.255.255 -j RETURN")
