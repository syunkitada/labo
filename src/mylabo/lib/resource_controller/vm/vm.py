import os
import xml.etree.ElementTree as ET
from xml import etree
import time
import logging

from mylabo.domain import resource
from mylabo.lib.runtime import node_context

LOG = logging.getLogger(__name__)


class VM(resource.Resource):
    def __init__(self, spec):
        self.spec = spec
        self.root_spec = spec["_root_spec"]
        self.c = node_context.NodeContext(spec)
        self.next = 0

        spec["_hostname"] = spec["name"].replace("_", "-") + "." + self.root_spec["spec"]["domain"]
        self.spec["spec"]["_vm_dir"] = os.path.join(self.root_spec["local_vms_dir"], spec["_hostname"])
        self.spec["spec"]["_image_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "img")
        self.spec["spec"]["_domain_xml_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "domain.xml")
        self.spec["spec"]["_monitor_socket_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "monitor.sock")
        self.spec["spec"]["_serial_socket_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "serial.sock")
        self.spec["spec"]["_serial_log_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "serial.log")
        self.spec["spec"]["_config_image_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "config.img")
        self.spec["spec"]["_metadata_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "meta-data")
        self.spec["spec"]["_userdata_path"] = os.path.join(self.spec["spec"]["_vm_dir"], "user-data")

        self.prepare_image()
        self.prepare_config_drive()
        self.prepare_domain_xml()

    def prepare_image(self):
        image = self.spec["spec"]["image"]
        lcmds = [
            f"mkdir -p {self.spec['spec']['_vm_dir']}",
            f"if [ ! -e {self.spec['spec']['_image_path']} ]; then",
        ]
        if image.startswith("local/"):
            src_image = os.path.join(self.root_spec["local_vm_images_dir"], image.replace("local/", ""))
            lcmds += [
                f"cp {src_image} {self.spec['spec']['_image_path']}",
            ]

        lcmds += [
            f"qemu-img resize --shrink {self.spec['spec']['_image_path']} {self.spec['spec']['disk']}G",
            "fi",
        ]

        self.c.exec(lcmds, title="prepare-vm", is_local=True)

    def prepare_config_drive(self):
        print("configdrive")
        metadata = []
        metadata += [f"hostname: {self.spec['_hostname']}"]
        with open(self.spec["spec"]["_metadata_path"], "w") as f:
            f.write("\n".join(metadata))

        userdata = []

        # userの設定
        userdata += [
            f"groupadd {self.spec['spec']['user']['name']}",
            f"useradd -g {self.spec['spec']['user']['group']} {self.spec['spec']['user']['name']}",
            f"echo '{self.spec['spec']['user']['name']}:{self.spec['spec']['user']['password']}' | chpasswd",
            f"mkdir -p /home/{self.spec['spec']['user']['name']}",
            f"chown -R {self.spec['spec']['user']['name']}:{self.spec['spec']['user']['group']} /home/{self.spec['spec']['user']['name']}",
            f"sed -i '$ i %{self.spec['spec']['user']['name']} ALL=(ALL) NOPASSWD:ALL' /etc/sudoers",
        ]

        # with open(f"/root/.ssh/labo.pem.pub", "r") as f:
        #     authorized_key = f.read()
        #     userdata += [
        #         f"mkdir -p /home/{self.spec['spec']['user']['name']}/.ssh",
        #         f'echo "{authorized_key}" > /home/{self.spec["spec"]["user"]["name"]}/.ssh/authorized_keys',
        #     ]

        for i, link in enumerate(self.spec["spec"].get("_links", [])):
            userdata += [
                f"dev{i}=`grep {link['peer_mac']} /sys/class/net/*/address -l | awk -F '/' '{{print $5}}'`",
                f"ip link set $dev{i} up",
            ]
            for inet in link.get("inets", []):
                userdata += [f"ip addr add {inet} dev $dev{i}"]

        for route in self.spec["spec"].get("routes", []):
            userdata += [f"ip route add {route['dst']} via {route['via']}"]

        if "resolvers" in self.spec["spec"]:
            userdata += [f"/opt/labo/bin/init-resolver {' '.join(self.spec['common']['resolvers'])}"]

        nfs = self.root_spec["spec"]["common"].get("nfs")
        if nfs is not None:
            userdata += [
                f"mkdir -p {nfs['path']}",
                f"until mount -t nfs {nfs['target']}:/ {nfs['path']}; do echo 'waiting for mount nfs'; sleep 2; done",
            ]

        with open(self.spec["spec"]["_userdata_path"], "w") as f:
            f.write("\n".join(userdata))

        self.c.exec(
            [
                f"genisoimage -o {self.spec['spec']['_config_image_path']} -V cidata"
                f" -r -J {self.spec['spec']['_metadata_path']} {self.spec['spec']['_userdata_path']}",
            ],
            title="prepare-vm",
            is_local=True,
        )

    def prepare_domain_xml(self):
        domain = ET.Element("domain", type="kvm")
        domain.set("xmlns:qemu", "http://libvirt.org/schemas/domain/qemu/1.0")

        #   <name>demo2</name>
        #   <uuid>4dea24b3-1d52-d8f3-2516-782e98a23fa0</uuid>
        #   <memory>131072</memory>
        #   <vcpu>1</vcpu>
        ET.SubElement(domain, "name").text = self.spec["_hostname"]
        # ET.SubElement(domain, "uuid").text = self.spec["_hostname"]
        ET.SubElement(domain, "memory").text = str(self.spec["spec"]["ram"] * 1024)  # in KiB
        ET.SubElement(domain, "vcpu").text = str(self.spec["spec"]["vcpus"])

        # <cpu mode='host-passthrough'>
        ET.SubElement(domain, "cpu", mode="host-passthrough")

        #   <os>
        #     <type arch="i686">hvm</type>
        #   </os>
        #   <clock sync="localtime"/>
        os_elem = ET.SubElement(domain, "os")
        type_elem = ET.SubElement(os_elem, "type", arch="x86_64")
        type_elem.text = "hvm"
        ET.SubElement(domain, "clock", sync="localtime")

        #   <devices>
        #     <emulator>/usr/bin/qemu-kvm</emulator>
        devices = ET.SubElement(domain, "devices")
        ET.SubElement(devices, "emulator").text = "/usr/bin/qemu-system-x86_64"

        #     <disk type='file' device='disk'>
        #       <source file='/var/lib/libvirt/images/demo2.img'/>
        #       <target dev='hda'/>
        #     </disk>
        disk = ET.SubElement(devices, "disk", type="file", device="disk")
        ET.SubElement(disk, "source", file=self.spec["spec"]["_image_path"])
        ET.SubElement(disk, "target", dev="vda")

        #     <interface type='ethernet'>
        #       <target dev='default'/>
        #       <mac address='24:42:53:21:52:45'/>
        #       <model type='virtio'/>
        #       <driver name='vhost' txmode='iothread' ioeventfd='on' event_idx='off' queues='5' rx_queue_size='256' tx_queue_size='256'/>
        #     </interface>
        for link in self.spec["spec"].get("_links", []):
            interface = ET.SubElement(devices, "interface", type="ethernet")
            ET.SubElement(interface, "target", dev=link["peer_name"] + "-tap")
            ET.SubElement(interface, "mac", address=link["peer_mac"])
            ET.SubElement(interface, "model", type="virtio")
            ET.SubElement(
                interface,
                "driver",
                name="vhost",
                txmode="iothread",
                ioeventfd="on",
                event_idx="off",
                queues="5",
                rx_queue_size="256",
                tx_queue_size="256",
            )

        # <qemu:commandline>
        #     <qemu:arg value='-device'/>
        #     <qemu:arg value='amd-iommu'/>
        # </qemu:commandline>
        commandline = ET.SubElement(domain, "qemu:commandline")
        ET.SubElement(commandline, "qemu:arg", value="-device")
        ET.SubElement(commandline, "qemu:arg", value="amd-iommu")

        #   </devices>

        tree = ET.ElementTree(domain)
        tree.write(self.spec["spec"]["_domain_xml_path"], encoding="utf-8")

        self.c.exec(
            [
                f"virsh undefine {self.spec['_hostname']}",
                f"virsh define {self.spec['spec']['_domain_xml_path']}",
            ],
            title="prepare-vm",
            is_local=True,
        )

        os._exit(0)

    def get(self, labels: dict = None):
        return {
            "name": self.spec["name"],
            "id": "dummy",
            "status": "unknown",
        }

    def apply(self):
        print("apply vm\n\n", self.spec)
        if self.next == 0:
            self._apply_prepare()
            self.next = 1
        elif self.next == 1:
            self._wait_for_active()
            self.next = 2
        elif self.next == 2:
            self._prepare()
            self.next = -1

    def delete(self):
        print("delete vm\n\n", self.spec)

    def _apply_prepare(self):
        print("Preparing VM...")

        # lcmds = [
        #     f"mkdir -p /mnt/nfs/mylabo/vms/{self.spec['_hostname']}",
        # ]
        # self.c.exec(lcmds, title="prepare-vm", is_local=True)

        # links = []
        # for link in self.spec["spec"]["_links"]:
        #     inets = []
        #     for peer_ip in link.get("peer_ips", []):
        #         inets.append(peer_ip["inet"])
        #     links.append(
        #         {
        #             "name": link["link_name"],
        #             "inets": inets,
        #             "mac": link["peer_mac"],
        #         }
        #     )

        # vm_yaml = {
        #     "image": self.spec["spec"]["image"],
        #     "vcpus": self.spec["spec"]["vcpus"],
        #     "ram": self.spec["spec"]["ram"],
        #     "disk": self.spec["spec"]["disk"],
        #     "links": links,
        #     "routes": self.spec["spec"].get("routes", []),
        #     "user": self.spec["spec"]["user"],
        #     "nfs": self.root_spec["spec"]["common"]["nfs"],
        #     "resolvers": self.root_spec["spec"]["common"].get("resolvers", []),
        # }
        # self.c.write(f"/mnt/nfs/vms/{self.spec['_hostname']}/vm.yaml", yaml=vm_yaml, is_local=True)

        # lcmds = [
        #     f"labo-vm-ctl start {self.spec['_hostname']}",
        # ]
        # self.c.exec(lcmds, title="prepare-vm", is_local=True)

    def _wait_for_active(self):
        print("Waiting for VM to become active...")
        # vmに疎通が取れるまでまつ
        # for i in range(1, 5):
        #     result = self.c.exec_without_log("ls", warn=True)
        #     if result.return_code == 0:
        #         break
        #     print(f"sleep {i * 2}")
        #     time.sleep(i * 2)

    def _prepare(self):
        print("Preparing VM...")
        # if "cmds" in self.spec["spec"]:
        #     self.c.exec(self.spec["spec"].get("cmds", []), title="cmds")

        # if "ansible" in self.spec["spec"]:
        #     self.c.ansible(self.spec["spec"]["ansible"])
