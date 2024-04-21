#!/opt/ansible-nonroot/bin/python3

import sys

from oslo_rootwrap import client


def main():
    cmd = sys.argv[1:]

    with open("/etc/ansible/rootwrap-socket-info", "rb") as f:
        socket_path = f.readline()[:-1].decode("utf-8")
        authkey = f.read(32)

    manager = client.ClientManager(socket_path, authkey)
    manager.connect()
    proxy = manager.rootwrap()
    return_code, stdout, stderr = proxy.run_one_command(cmd, None)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    exit(return_code)


if __name__ == "__main__":
    main()
