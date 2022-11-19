# qemu utils

import time
import os


def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(rspec)
    elif cmd == "make":
        make(c, spec, rspec)
    elif cmd == "clean":
        clean(c, rspec)
    elif cmd == "remake":
        clean(c, rspec)
        make(c, spec, rspec)
    elif cmd == "stop":
        stop(c, rspec)
    elif cmd == "restart":
        stop(c, rspec)
        make(c, spec, rspec)
    elif cmd == "log":
        with open(rspec["_serial_log_path"]) as f:
            print(f.read())
    elif cmd == "console":
        c.sudo(f"minicom -D unix#{rspec['_serial_socket_path']}", pty=True)
    elif cmd == "monitor":
        c.sudo(f"minicom -D unix#{rspec['_monitor_socket_path']}", pty=True)
    else:
        print(
            """# vm help
-t vm:{0} -c dump
-t vm:{0} -c make
-t vm:{0} -c clean
-t vm:{0} -c remake
-t vm:{0} -c stop
-t vm:{0} -c restart
-t vm:{0} -c log
-t vm:{0} -c console
-t vm:{0} -c monitor
""".format(
                rspec["name"]
            )
        )


def make(c, spec, rspec):
    os.makedirs(rspec["_vm_dir"], exist_ok=True)
    _make_config_drive(c, spec, rspec)
    _make_qemu(c, spec, rspec)


def clean(c, rspec):
    stop(c, rspec)
    c.sudo(f"rm -rf {rspec['_vm_dir']}")


def stop(c, rspec):
    result = grep_qemu(c, rspec)
    if result.ok:
        c.sudo(f"kill {result.pid}")


def _make_config_drive(c, spec, rspec):
    print("configdrive")
    metadata = []
    metadata += [f"hostname: {rspec['_hostname']}"]
    with open(rspec["_metadata_path"], "w") as f:
        f.write("\n".join(metadata))

    userdata = []

    # userの設定
    userdata += [
        "groupadd admin",
        "useradd -g admin admin",
        "echo 'admin:admin' | chpasswd",
        "mkdir -p /home/admin",
        "chown -R admin:admin /home/admin",
        "sed -i '$ i %admin ALL=(ALL) ALL' /etc/sudoers",
    ]

    for i, link in enumerate(rspec.get("_links", [])):
        userdata += [
            f"dev{i}=`grep {link['peer_mac']} /sys/class/net/*/address -l | awk -F '/' '{{print $5}}'`",
            f"ip link set $dev{i} up",
        ]
        for ip in link.get("peer_ips", []):
            userdata += [f"ip addr add {ip['inet']} dev $dev{i}"]

    # setup routes
    for to, route in rspec.get("routes", {}).items():
        userdata += [f"ip route add {to} via {route}"]

    # osによって挙動を変える場合
    if rspec["_image"]["base"] == "centos7":
        # setup resolver
        userdata += ["cat << 'EOS' > /etc/resolv.conf"]
        for resolver in rspec.get("resolvers", []):
            userdata += [f"nameserver {resolver}"]
        userdata += ["EOS"]
    elif rspec["_image"]["base"] in ["ubuntu20", "ubuntu22"]:
        userdata += [
            "mkdir -p /etc/systemd/resolved.conf.d/",
            "cat << 'EOT' > /etc/systemd/resolved.conf.d/labo.conf",
        ]
        for resolver in rspec.get("resolvers", []):
            userdata += [
                "[Resolve]",
                f"DNS={resolver}",
                # FallbackDNS=
                # Domains=
                "LLMNR=no",
                "MulticastDNS=no",
                "DNSSEC=no",
                "Cache=yes",
                "DNSStubListener=yes",
            ]
        userdata += [
            "EOT",
            "systemctl enable systemd-resolved",
            "systemctl restart systemd-resolved",
        ]

    nfs = rspec.get("nfs")
    if nfs is not None:
        userdata += [
            f"mkdir -p {nfs['path']}",
            f"mount -t nfs {nfs['target']}:/ {nfs['path']}",
        ]

    with open(rspec["_userdata_path"], "w") as f:
        f.write("\n".join(userdata))

    c.sudo(f"genisoimage -o {rspec['_config_image_path']} -V cidata -r -J {rspec['_metadata_path']} {rspec['_userdata_path']}")


def grep_qemu(c, rspec):
    result = c.sudo(f"ps -ax | grep -v sudo | grep [q]emu-system-x86_64 | grep '/{rspec['name']}/'", warn=True, hide=True)
    if result.ok:
        result.pid = result.stdout.split()[0]
    return result


def _make_qemu(c, spec, rspec):
    if not os.path.exists(rspec["_image_path"]):
        c.sudo(f"cp {rspec['_image']['_path']} {rspec['_image_path']}")
        c.sudo(f"qemu-img resize --shrink {rspec['_image_path']} {rspec['disk']}G")

    grep_qemu_result = grep_qemu(c, rspec)
    if grep_qemu_result.failed:
        qemu_cmd = ["qemu-system-x86_64"]
        qemu_cmd += [
            "-enable-kvm -machine q35,accel=kvm",
            "-cpu host",
            f"-smp cores={rspec['vcpus']}",
            f"-m {rspec['ram']}M,slots=64,maxmem=1024G",
            f"-object memory-backend-file,id=mem1,size={rspec['ram']}M,mem-path=/dev/hugepages/{rspec['name']},host-nodes=0,policy=bind",
            "-numa node,nodeid=0,memdev=mem1",
            f"-drive id=bootdisk1,file={rspec['_image_path']},if=none",
            "-device virtio-blk-pci,scsi=off,drive=bootdisk1,bootindex=1",
            f"-drive file={rspec['_config_image_path']},format=raw,if=none,id=drive-ide0-1-0,readonly=on",
            "-device amd-iommu",
            "-device ide-cd,bus=ide.1,unit=0,drive=drive-ide0-1-0,id=ide0-1-0",
            f"-monitor unix:{rspec['_monitor_socket_path']},server,nowait",
            f"-serial unix:{rspec['_serial_socket_path']},server,nowait,logfile={rspec['_serial_log_path']}",
            "-nographic",
        ]
        nic_options = []
        for link in rspec.get("_links", []):
            nic_options += [
                f"-nic tap,ifname={link['peer_name']},model=virtio-net-pci,mac={link['peer_mac']},script=no,script=no,downscript=no"
            ]
        qemu_cmd += nic_options
        c.sudo(
            " ".join(qemu_cmd),
            asynchronous=True,
        )

        time.sleep(2)
        grep_qemu_result = grep_qemu(c, rspec)

    if grep_qemu_result.ok:
        for link in rspec.get("_links", []):
            c.sudo(f"ip link set {link['peer_name']} up")
            c.sudo(f"ip link set dev {link['peer_name']} master {link['src_name']}")
