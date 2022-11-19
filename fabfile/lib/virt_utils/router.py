# router utils

import ipaddress


def make_gw(c, spec, rspec):
    # setup bridge
    br = c.sudo(f"ip addr show '{rspec['name']}'", hide=True, warn=True)
    if br.failed:
        c.sudo(f"ip link add {rspec['name']} type bridge")

    if rspec["ip"] not in br.stdout:
        c.sudo(f"ip addr add dev '{rspec['name']}' {rspec['ip']}")
        c.sudo(f"ip link set '{rspec['name']}' up")

    ip = ipaddress.ip_interface(rspec["ip"])

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
        c.sudo(f"iptables -t nat -A POSTROUTING -p TCP -s {rspec['ip']} ! -d {rspec['ip']} -j MASQUERADE --to-ports 30000-40000")
    if masqueradeUdpMap.get(ip.network) is None:
        c.sudo(f"iptables -t nat -A POSTROUTING -p UDP -s {rspec['ip']} ! -d {rspec['ip']} -j MASQUERADE --to-ports 30000-40000")
    if returnMap.get(ip.network) is None:
        c.sudo(f"iptables -t nat -A POSTROUTING -s {rspec['ip']} -d 255.255.255.255 -j RETURN")
