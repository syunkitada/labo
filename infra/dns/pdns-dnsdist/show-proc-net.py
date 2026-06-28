#!/usr/bin/env python3
"""
Parse /proc/net/tcp and /proc/net/udp to display network connections in human-readable format.
"""

import os
import sys
from typing import List, Dict

# TCP/UDP states mapping
TCP_STATES = {
    "01": "ESTABLISHED",
    "02": "SYN_SENT",
    "03": "SYN_RECV",
    "04": "FIN_WAIT1",
    "05": "FIN_WAIT2",
    "06": "TIME_WAIT",
    "07": "CLOSE",
    "08": "CLOSE_WAIT",
    "09": "LAST_ACK",
    "0A": "LISTEN",
    "0B": "CLOSING",
}


def hex_to_ip(hex_str: str) -> str:
    """Convert hex IP address to dotted decimal notation."""
    # Remove any whitespace
    hex_str = hex_str.strip()

    # Handle IPv4 (8 hex characters)
    if len(hex_str) == 8:
        # Reverse byte order for little-endian
        parts = []
        for i in range(0, 8, 2):
            parts.append(hex_str[i : i + 2])
        parts.reverse()
        return ".".join(str(int(part, 16)) for part in parts)

    # Handle IPv6 (32 hex characters)
    elif len(hex_str) == 32:
        # Convert to standard IPv6 notation
        parts = []
        for i in range(0, 32, 8):
            chunk = hex_str[i : i + 8]
            # Reverse byte order within each 4-byte chunk
            reversed_chunk = "".join([chunk[j : j + 2] for j in range(0, 8, 2)][::-1])
            parts.append(reversed_chunk)

        # Join and format as IPv6
        ipv6 = ":".join(
            [
                (
                    parts[i : i + 2][0] + parts[i : i + 2][1]
                    if i + 1 < len(parts)
                    else parts[i]
                )
                for i in range(0, len(parts), 2)
            ]
        )

        # Simplify IPv6 notation
        ipv6_parts = []
        for i in range(0, len(hex_str), 4):
            ipv6_parts.append(hex_str[i : i + 4])

        # Reverse for proper byte order
        result = []
        for i in range(0, 32, 8):
            chunk = hex_str[i : i + 8]
            word1 = chunk[6:8] + chunk[4:6]
            word2 = chunk[2:4] + chunk[0:2]
            result.append(word1 + word2)

        return ":".join(result)

    return hex_str


def parse_address(addr: str) -> tuple:
    """Parse address:port from hex format."""
    parts = addr.split(":")
    if len(parts) != 2:
        return ("unknown", 0)

    ip = hex_to_ip(parts[0])
    port = int(parts[1], 16)
    return (ip, port)


def parse_proc_net_file(filepath: str, protocol: str) -> List[Dict]:
    """Parse /proc/net/tcp or /proc/net/udp file."""
    results = []

    if not os.path.exists(filepath):
        return results

    try:
        with open(filepath, "r") as f:
            lines = f.readlines()

        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 10:
                continue

            # Parse fields
            local_addr, local_port = parse_address(parts[1])
            remote_addr, remote_port = parse_address(parts[2])
            state = parts[3]
            state_name = TCP_STATES.get(state, f"UNKNOWN({state})")

            # tx_queue:rx_queue
            tx_queue, rx_queue = parts[4].split(":")
            tx_queue = int(tx_queue, 16)
            rx_queue = int(rx_queue, 16)

            # UID
            uid = int(parts[7])

            # Inode
            inode = int(parts[9])

            results.append(
                {
                    "protocol": protocol,
                    "local_addr": local_addr,
                    "local_port": local_port,
                    "remote_addr": remote_addr,
                    "remote_port": remote_port,
                    "state": state_name,
                    "tx_queue": tx_queue,
                    "rx_queue": rx_queue,
                    "uid": uid,
                    "inode": inode,
                }
            )

    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)

    return results


def format_address(addr: str, port: int) -> str:
    """Format address and port for display."""
    # Replace 0.0.0.0 with * for listening sockets
    if addr == "0.0.0.0":
        addr = "*"
    elif addr == "0:0:0:0:0:0:0:0" or addr == "::":
        addr = "*"

    # Replace 0.0.0.0:0 with *:*
    if addr == "*" and port == 0:
        return "*:*"

    # IPv6 addresses need brackets
    if ":" in addr and addr != "*":
        return f"[{addr}]:{port}"

    return f"{addr}:{port}"


def display_connections(connections: List[Dict], protocol: str, show_all: bool = False):
    """Display connections in a formatted table."""
    if not connections:
        return

    # Filter listening connections if show_all is False
    if not show_all:
        connections = [
            c for c in connections if c["state"] == "LISTEN" or protocol == "UDP"
        ]

    if not connections:
        return

    print(f"\n{'='*100}")
    print(f"{protocol} Connections:")
    print(f"{'='*100}")
    print(
        f"{'Local Address':<30} {'Remote Address':<30} {'State':<15} {'UID':<8} {'Queues'}"
    )
    print(f"{'-'*100}")

    for conn in connections:
        local = format_address(conn["local_addr"], conn["local_port"])
        remote = format_address(conn["remote_addr"], conn["remote_port"])
        state = conn["state"]
        uid = conn["uid"]
        queues = f"TX:{conn['tx_queue']} RX:{conn['rx_queue']}"

        print(f"{local:<30} {remote:<30} {state:<15} {uid:<8} {queues}")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse /proc/net/tcp and /proc/net/udp to display network connections"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Show all connections (not just listening)",
    )
    parser.add_argument(
        "-l",
        "--listen",
        action="store_true",
        help="Show only LISTEN state connections",
    )
    parser.add_argument(
        "-t", "--tcp", action="store_true", help="Show only TCP connections"
    )
    parser.add_argument(
        "-u", "--udp", action="store_true", help="Show only UDP connections"
    )
    parser.add_argument(
        "-4", "--ipv4", action="store_true", help="Show only IPv4 connections"
    )
    parser.add_argument(
        "-6", "--ipv6", action="store_true", help="Show only IPv6 connections"
    )

    args = parser.parse_args()

    # If no protocol specified, show both
    show_tcp = args.tcp or not args.udp
    show_udp = args.udp or not args.tcp

    # If no IP version specified, show both
    show_ipv4 = args.ipv4 or not args.ipv6
    show_ipv6 = args.ipv6 or not args.ipv4

    all_connections = []

    # Parse TCP
    if show_tcp:
        if show_ipv4:
            tcp_connections = parse_proc_net_file("/proc/net/tcp", "TCP")
            all_connections.extend(tcp_connections)
        if show_ipv6:
            tcp6_connections = parse_proc_net_file("/proc/net/tcp6", "TCP6")
            all_connections.extend(tcp6_connections)

    # Parse UDP
    if show_udp:
        if show_ipv4:
            udp_connections = parse_proc_net_file("/proc/net/udp", "UDP")
            all_connections.extend(udp_connections)
        if show_ipv6:
            udp6_connections = parse_proc_net_file("/proc/net/udp6", "UDP6")
            all_connections.extend(udp6_connections)

    # Filter by state if --listen is specified
    if args.listen:
        all_connections = [c for c in all_connections if c["state"] == "LISTEN"]

    # Group by protocol
    protocols = {}
    for conn in all_connections:
        proto = conn["protocol"]
        if proto not in protocols:
            protocols[proto] = []
        protocols[proto].append(conn)

    # Display results
    for proto in sorted(protocols.keys()):
        display_connections(protocols[proto], proto, args.all)

    if not all_connections:
        print("No connections found or unable to read /proc/net files.")
        print("You may need to run this script with appropriate permissions.")


if __name__ == "__main__":
    main()
