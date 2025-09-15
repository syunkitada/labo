import os
import xml.etree.ElementTree as ET
import logging

from mylabo.domain import resource
from mylabo.lib.runtime import node_context
from mylabo.lib.context import context

LOG = logging.getLogger(__name__)


class VM(resource.Resource):
    def __init__(self, ctx: context.Context, manifest: dict):
        self.ctx = ctx
        self.c = node_context.NodeContext(manifest)
        self.manifest = manifest
        self.spec = manifest["spec"]
        self.root_manifest = manifest["_root_manifest"]
        self.next = 0
        self.complete_spec()

    def complete_spec(self):
        spec = self.manifest
        spec["spec"]["_vm_dir"] = os.path.join(self.root_manifest["local_vms_dir"], spec["_hostname"])
        spec["spec"]["_image_path"] = os.path.join(spec["spec"]["_vm_dir"], "img")
        spec["spec"]["_domain_xml_path"] = os.path.join(spec["spec"]["_vm_dir"], "domain.xml")
        spec["spec"]["_monitor_socket_path"] = os.path.join(spec["spec"]["_vm_dir"], "monitor.sock")
        spec["spec"]["_serial_socket_path"] = os.path.join(spec["spec"]["_vm_dir"], "serial.sock")
        spec["spec"]["_serial_log_path"] = os.path.join(self.spec["_vm_dir"], "serial.log")
        spec["spec"]["_config_image_path"] = os.path.join(self.spec["_vm_dir"], "config.img")
        spec["spec"]["_metadata_path"] = os.path.join(self.spec["_vm_dir"], "meta-data")
        spec["spec"]["_userdata_path"] = os.path.join(self.spec["_vm_dir"], "user-data")

    def prepare_image(self):
        image = self.spec["image"]
        lcmds = [
            f"mkdir -p {self.manifest['spec']['_vm_dir']}",
            f"if [ ! -e {self.manifest['spec']['_image_path']} ]; then",
        ]
        if image.startswith("local/"):
            src_image = os.path.join(self.root_manifest["local_vm_images_dir"], image.replace("local/", ""))
            lcmds += [
                f"cp {src_image} {self.manifest['spec']['_image_path']}",
            ]

        lcmds += [
            f"qemu-img resize --shrink {self.manifest['spec']['_image_path']} {self.manifest['spec']['disk']}G",
            "fi",
        ]

        self.c.exec(lcmds, title="prepare-vm", is_local=True)

    def prepare_config_drive(self):
        print("configdrive")
        metadata = []
        metadata += [f"hostname: {self.manifest['_hostname']}"]
        with open(self.spec["_metadata_path"], "w") as f:
            f.write("\n".join(metadata))

        userdata = []

        # userの設定
        userdata += [
            f"groupadd {self.manifest['spec']['user']['name']}",
            f"useradd -g {self.manifest['spec']['user']['group']} {self.manifest['spec']['user']['name']}",
            f"echo '{self.manifest['spec']['user']['name']}:{self.manifest['spec']['user']['password']}' | chpasswd",
            f"mkdir -p /home/{self.manifest['spec']['user']['name']}",
            f"chown -R {self.manifest['spec']['user']['name']}:{self.manifest['spec']['user']['group']} /home/{self.manifest['spec']['user']['name']}",
            f"sed -i '$ i %{self.manifest['spec']['user']['name']} ALL=(ALL) NOPASSWD:ALL' /etc/sudoers",
        ]

        # with open(f"/root/.ssh/labo.pem.pub", "r") as f:
        #     authorized_key = f.read()
        #     userdata += [
        #         f"mkdir -p /home/{self.manifest['spec']['user']['name']}/.ssh",
        #         f'echo "{authorized_key}" > /home/{self.spec["user"]["name"]}/.ssh/authorized_keys',
        #     ]

        for i, link in enumerate(self.spec.get("_links", [])):
            userdata += [
                f"dev{i}=`grep {link['peer_mac']} /sys/class/net/*/address -l | awk -F '/' '{{print $5}}'`",
                f"ip link set $dev{i} up",
            ]

            for inet in link.get("peer_ips", []):
                userdata += [f"ip addr add {inet['inet']} dev $dev{i}"]

        for route in self.spec.get("routes", []):
            userdata += [f"ip route add {route['dst']} via {route['via']}"]

        if "resolvers" in self.spec:
            userdata += [f"/opt/labo/bin/init-resolver {' '.join(self.manifest['common']['resolvers'])}"]

        # nfs = self.root_manifest["spec"]["common"].get("nfs")
        # if nfs is not None:
        #     userdata += [
        #         f"mkdir -p {nfs['path']}",
        #         f"until mount -t nfs {nfs['target']}:/ {nfs['path']}; do echo 'waiting for mount nfs'; sleep 2; done",
        #     ]

        with open(self.spec["_userdata_path"], "w") as f:
            f.write("\n".join(userdata))

        self.c.exec(
            [
                f"genisoimage -o {self.manifest['spec']['_config_image_path']} -V cidata"
                f" -r -J {self.manifest['spec']['_metadata_path']} {self.manifest['spec']['_userdata_path']}",
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
        ET.SubElement(domain, "name").text = self.manifest["_hostname"]
        # ET.SubElement(domain, "uuid").text = self.manifest["_hostname"]
        ET.SubElement(domain, "memory").text = str(self.spec["ram"] * 1024)  # in KiB
        ET.SubElement(domain, "vcpu").text = str(self.spec["vcpus"])

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

        # <disk type='file' device='disk'>
        #   <driver name='qemu' type='qcow2' cache='none'/>
        #   <source file='/var/lib/nova/instances/88043986-97f8-416f-ada9-6eee22081a3d/disk' index='2'/>
        #   <backingStore type='file' index='3'>
        #     <format type='raw'/>
        #     <source file='/var/lib/nova/instances/_base/19fe8a7a85738170b42956bdd2cb36887a939353'/>
        #     <backingStore/>
        #   </backingStore>
        #   <target dev='vda' bus='virtio'/>
        #   <alias name='virtio-disk0'/>
        #   <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
        # </disk>
        root_disk = ET.SubElement(devices, "disk", type="file", device="disk")
        ET.SubElement(root_disk, "driver", name="qemu", type="qcow2", cache="none")
        ET.SubElement(root_disk, "source", file=self.spec["_image_path"], index="2")
        # backing_store = ET.SubElement(root_disk, "backingStore", type="file", index="3")
        # ET.SubElement(backing_store, "format", type="raw")
        # ET.SubElement(backing_store, "source", file=self.spec["_base_image_path"])
        # ET.SubElement(backing_store, "backingStore")
        ET.SubElement(root_disk, "target", dev="vda", bus="virtio")
        ET.SubElement(root_disk, "alias", name="virtio-disk0")
        ET.SubElement(root_disk, "address", type="pci", domain="0x0000", bus="0x00", slot="0x04", function="0x0")

        # <disk type='file' device='cdrom'>
        #   <driver name='qemu' type='raw' cache='none'/>
        #   <source file='/var/lib/nova/instances/88043986-97f8-416f-ada9-6eee22081a3d/disk.config' index='1'/>
        #   <backingStore/>
        #   <target dev='hda' bus='ide'/>
        #   <readonly/>
        #   <alias name='ide0-0-0'/>
        #   <address type='drive' controller='0' bus='0' target='0' unit='0'/>
        # </disk>
        config_drive = ET.SubElement(devices, "disk", type="file", device="cdrom")
        ET.SubElement(config_drive, "driver", name="qemu", type="raw", cache="none")
        ET.SubElement(config_drive, "source", file=self.spec["_config_image_path"], index="1")
        ET.SubElement(config_drive, "backingStore")
        ET.SubElement(config_drive, "target", dev="hda", bus="ide")
        ET.SubElement(config_drive, "readonly")
        ET.SubElement(config_drive, "alias", name="ide0-0-0")
        ET.SubElement(config_drive, "address", type="drive", controller="0", bus="0", target="0", unit="0")

        #     <interface type='ethernet'>
        #       <target dev='default'/>
        #       <mac address='24:42:53:21:52:45'/>
        #       <model type='virtio'/>
        #       <driver name='vhost' txmode='iothread' ioeventfd='on' event_idx='off' queues='5' rx_queue_size='256' tx_queue_size='256'/>
        #     </interface>
        for link in self.spec.get("_links", []):
            interface = ET.SubElement(devices, "interface", type="ethernet")
            ET.SubElement(interface, "target", dev=link["peer_name"])
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

        # <serial type='pty'>
        #   <source path='/dev/pts/1'/>
        #   <log file='/var/lib/nova/instances/b3166191-f34e-46b2-af27-8155734d82b3/console.log' append='off'/>
        #   <target type='isa-serial' port='0'>
        #     <model name='isa-serial'/>
        #   </target>
        #   <alias name='serial0'/>
        # </serial>
        serial = ET.SubElement(devices, "serial", type="pty")
        ET.SubElement(serial, "source")
        ET.SubElement(serial, "log", file=self.spec["_serial_log_path"], append="off")
        serial_target = ET.SubElement(serial, "target", type="isa-serial", port="0")
        ET.SubElement(serial_target, "model", name="isa-serial")
        ET.SubElement(serial, "alias", name="serial0")

        # <console type='pty' tty='/dev/pts/1'>
        #   <source path='/dev/pts/1'/>
        #   <log file='/var/lib/nova/instances/b3166191-f34e-46b2-af27-8155734d82b3/console.log' append='off'/>
        #   <target type='serial' port='0'/>
        #   <alias name='serial0'/>
        # </console>
        console = ET.SubElement(devices, "console", type="pty")
        ET.SubElement(console, "source")
        ET.SubElement(console, "log", file=self.spec["_serial_log_path"], append="off")
        ET.SubElement(console, "target", type="serial", port="0")
        ET.SubElement(console, "alias", name="serial0")

        # <qemu:commandline>
        #     <qemu:arg value='-device'/>
        #     <qemu:arg value='amd-iommu'/>
        # </qemu:commandline>
        # commandline = ET.SubElement(domain, "qemu:commandline")
        # ET.SubElement(commandline, "qemu:arg", value="-device")
        # ET.SubElement(commandline, "qemu:arg", value="amd-iommu")

        #   </devices>

        ET.SubElement(domain, "audio", type="none")

        tree = ET.ElementTree(domain)
        tree.write(self.spec["_domain_xml_path"], encoding="utf-8")

    def get(self):
        return {
            "name": self.manifest["name"],
            "id": "dummy",
            "status": "unknown",
        }

    def apply(self):
        print("apply vm\n\n", self.manifest)
        if self.next == 0:
            self._apply_prepare()
            self.next = 1
        elif self.next == 1:
            self._wait_for_active()
            self.next = 2
        elif self.next == 2:
            self._prepare()
            self.next = -1

    def any(self, action: resource.AnyAction):
        print("stop vm\n\n", self.manifest)

    def test(self):
        print("test vm\n\n", self.manifest)

    def delete(self):
        self.c.exec(
            [
                f"if virsh list | grep {self.manifest['_hostname']}; then",
                f"  virsh destroy {self.manifest['_hostname']}",
                "fi",
                f"if virsh list --all | grep {self.manifest['_hostname']}; then",
                f"  virsh undefine {self.manifest['_hostname']}",
                "fi",
                f"rm -rf {self.manifest['spec']['_vm_dir']}",
            ],
            title="delete-vm",
            is_local=True,
        )

    def _apply_prepare(self):
        print("Preparing VM...")
        self.prepare_image()
        self.prepare_config_drive()
        self.prepare_domain_xml()

        self.c.exec(
            [
                f"if virsh list | grep {self.manifest['_hostname']}; then",
                f"  virsh destroy {self.manifest['_hostname']}",
                "fi",
                f"if virsh list --all | grep {self.manifest['_hostname']}; then",
                f"  virsh undefine {self.manifest['_hostname']}",
                "fi",
                f"virsh define {self.manifest['spec']['_domain_xml_path']}",
                f"virsh start {self.manifest['_hostname']}",
            ],
            title="prepare-vm",
            is_local=True,
        )

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
        # if "cmds" in self.spec:
        #     self.c.exec(self.spec.get("cmds", []), title="cmds")

        # if "ansible" in self.spec:
        #     self.c.ansible(self.spec["ansible"])
