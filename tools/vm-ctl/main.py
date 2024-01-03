#!/usr/bin/env python3

from collections import OrderedDict
import re
import subprocess
import yaml
import os
import argparse
p = argparse.ArgumentParser()
p.add_argument('action', choices=[
    'start', 'recreate', 'stop',
    'console', 'console-log', 'monitor',
    'list', 'delete',
], help='action')
p.add_argument('vm_name', help='vm name', nargs='*', default=[])
args = p.parse_args()

if args.action == "start" or args.action == "stop" or args.action == "delete":
    if len(args.vm_name) == 0:
        p.error("start, delete action require image_name")

IMAGE_ROOT = '/mnt/nfs/vm_images/'
VM_ROOT = '/mnt/nfs/vms/'


def main():
    if args.action == "list":
        list()
    elif args.action == "start":
        start()
    elif args.action == "stop":
        stop()
    elif args.action == "delete":
        delete()
    elif args.action == "console":
        console()
    elif args.action == "console-log":
        console_log()

def list():
    vms = OrderedDict()
    vm_dirs = os.listdir(VM_ROOT)
    for vm_dir in vm_dirs:
        vms[vm_dir] = {
            'status': 'stopped',
        }

    result = subprocess.run(["bash", "-c", "ps ax | grep '[q]emu-system'"], capture_output=True)
    for line in result.stdout.splitlines():
        line = line.decode('utf-8') 
        bootdisk = re.findall('-drive id=bootdisk1,file=(.*),if=none ', line)
        if len(bootdisk) != 1:
            continue
        splited_bootdisk = bootdisk[0].split("/")
        vm_name = splited_bootdisk[-2]
        if vm_name in vms:
            vms[vm_name]['status'] = 'active'

    for name, vm in vms.items():
        print(name, vm)

def delete():
    stop()
    cmds = ["rm", "-rf", os.path.join(VM_ROOT, args.vm_name[0])]
    subprocess.run(cmds)

def stop():
    cmds = ["systemctl", "stop", args.vm_name[0]]
    subprocess.run(cmds)

def start():
    for name in args.vm_name:
        vm_dir = os.path.join(VM_ROOT, name)
        vm_yaml = os.path.join(vm_dir, 'vm.yaml')
        if os.path.exists(vm_yaml):
            spec = None
            with open(vm_yaml) as f:
                spec = yaml.safe_load(f)
            spec['_name'] = name
            spec["_image_path"] = os.path.join(vm_dir, "img")
            spec["_monitor_socket_path"] = os.path.join(vm_dir, "monitor.sock")
            spec["_serial_socket_path"] = os.path.join(vm_dir, "serial.sock")
            spec["_serial_log_path"] = os.path.join(vm_dir, "serial.log")
            spec["_config_image_path"] = os.path.join(vm_dir, "config.img")
            spec["_metadata_path"] = os.path.join(vm_dir, "meta-data")
            spec["_userdata_path"] = os.path.join(vm_dir, "user-data")
            make_config_drive(spec)
            start_vm(spec)


def check_vm_exists(spec):
    result = subprocess.run(["bash", "-c", f"ps -ax | grep -v sudo | grep [q]emu-system-x86_64 | grep '/{spec['_name']}/'"])
    if result.returncode == 1:
        return False
    return True


def start_vm(spec):
    print("start_vm")
    print(spec)
    if not os.path.exists(spec["_image_path"]):
        src_image = os.path.join(IMAGE_ROOT, spec["image"])
        subprocess.run(["cp", src_image, spec['_image_path']])
        subprocess.run(["qemu-img", "resize", "--shrink", spec['_image_path'], f"{spec['disk']}G"])
    if check_vm_exists(spec):
        print("vm exists")
        return

    print("vm start")

    qemu_cmd = ["qemu-system-x86_64"]
    qemu_cmd += [
        "-enable-kvm",
        "-machine", "q35,accel=kvm",
        "-cpu", "host",
        "-smp", f"cores={spec['vcpus']}",
        "-m", f"{spec['ram']}M,slots=64,maxmem=1024G",
        "-object", f"memory-backend-file,id=mem1,size={spec['ram']}M,mem-path=/dev/hugepages/{spec['_name']},host-nodes=0,policy=bind",
        "-numa", "node,nodeid=0,memdev=mem1",
        "-drive", f"id=bootdisk1,file={spec['_image_path']},if=none",
        "-device", "virtio-blk-pci,scsi=off,drive=bootdisk1,bootindex=1",
        "-drive", f"file={spec['_config_image_path']},format=raw,if=none,id=drive-ide0-1-0,readonly=on",
        "-device", "amd-iommu",
        "-device", "ide-cd,bus=ide.1,unit=0,drive=drive-ide0-1-0,id=ide0-1-0",
        "-monitor", f"unix:{spec['_monitor_socket_path']},server,nowait",
        "-serial", f"unix:{spec['_serial_socket_path']},server,nowait,logfile={spec['_serial_log_path']}",
        "-nographic",
    ]
    nic_options = []
    for _, link in enumerate(spec.get("links", [])):
        nic_options += [
            "-nic", f"tap,ifname={link['name']},model=virtio-net-pci,mac={link['mac']},script=no,script=no,downscript=no"
        ]

    qemu_cmd += nic_options
    subprocess.run(["systemctl", "reset-failed", spec['_name']])
    cmds = ["systemd-run", "--unit", spec['_name'], '--'] + qemu_cmd
    print(cmds)
    subprocess.run(cmds)

def console():
    name = args.vm_name[0]
    vm_dir = os.path.join(VM_ROOT, name)
    spec = {}
    spec["_serial_socket_path"] = os.path.join(vm_dir, "serial.sock")
    subprocess.run(["minicom", "-D", f"unix#{spec['_serial_socket_path']}"])

def console_log():
    name = args.vm_name[0]
    vm_dir = os.path.join(VM_ROOT, name)
    spec = {}
    spec["_serial_log_path"] = os.path.join(vm_dir, "serial.log")
    with open(spec["_serial_log_path"]) as f:
        print(f.read())

def monitor(spec):
    subprocess.run(["minicom", "-D", f"unix#{spec['_monitor_socket_path']}"])

def make_config_drive(spec):
    print("configdrive")
    metadata = []
    metadata += [f"hostname: {spec['_name']}"]
    with open(spec["_metadata_path"], "w") as f:
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

    for i, link in enumerate(spec.get("links", [])):
        userdata += [
            f"dev{i}=`grep {link['mac']} /sys/class/net/*/address -l | awk -F '/' '{{print $5}}'`",
            f"ip link set $dev{i} up",
        ]
        for inet in link.get("inets", []):
            userdata += [f"ip addr add {inet} dev $dev{i}"]

    # setup routes
    for route in spec.get("routes", []):
        userdata += [f"ip route add {route['dst']} via {route['via']}"]

    # # osによって挙動を変える場合
    # if rspec["_image"]["base"] == "centos7":
    #     # setup resolver
    #     userdata += ["cat << 'EOS' > /etc/resolv.conf"]
    #     for resolver in rspec.get("resolvers", []):
    #         userdata += [f"nameserver {resolver}"]
    #     userdata += ["EOS"]
    # elif rspec["_image"]["base"] in ["ubuntu20", "ubuntu22"]:
    #     userdata += [
    #         "mkdir -p /etc/systemd/resolved.conf.d/",
    #         "cat << 'EOT' > /etc/systemd/resolved.conf.d/labo.conf",
    #     ]
    #     for resolver in rspec.get("resolvers", []):
    #         userdata += [
    #             "[Resolve]",
    #             f"DNS={resolver}",
    #             # FallbackDNS=
    #             # Domains=
    #             "LLMNR=no",
    #             "MulticastDNS=no",
    #             "DNSSEC=no",
    #             "Cache=yes",
    #             "DNSStubListener=yes",
    #         ]
    #     userdata += [
    #         "EOT",
    #         "systemctl enable systemd-resolved",
    #         "systemctl restart systemd-resolved",
    #     ]

    # resize ext4
    # userdata += [
    #     # 初回起動時は実際のスペースが異なるのでFixする必要がある
    #     # Warning: Not all of the space available to /dev/vda appears to be used, ... Fix/Ignore?
    #     "parted '/dev/vda' ---pretend-input-tty <<EOF",
    #     "resizepart",
    #     "Fix",
    #     "quit",
    #     "EOF",
    #     # 空きをすべて割り当てる
    #     "parted '/dev/vda' ---pretend-input-tty <<EOF",
    #     "resizepart",
    #     "1",
    #     "Yes",
    #     "100%",
    #     "quit",
    #     "EOF",
    #     # ext4のオンラインリサイズ
    #     "resize2fs /dev/vda1",
    # ]

    nfs = spec.get("nfs")
    if nfs is not None:
        userdata += [
            f"mkdir -p {nfs['path']}",
            f"mount -t nfs {nfs['target']}:/ {nfs['path']}",
        ]

    with open(spec["_userdata_path"], "w") as f:
        f.write("\n".join(userdata))

    subprocess.run(["genisoimage", "-o", spec['_config_image_path'], "-V", "cidata", "-r", "-J", spec['_metadata_path'], spec['_userdata_path']])


if __name__ == "__main__":
    main()
