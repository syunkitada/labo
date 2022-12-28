import os


def cmd(t):
    if t.cmd == "make":
        _make(t)
    elif t.cmd == "clean":
        _clean(t)
    elif t.cmd == "remake":
        _clean(t)
        _make(t)


def _make(t):
    if os.path.exists(t.rspec["_path"]):
        return
    if "url" in t.rspec:
        _download(t)
    if "base" in t.rspec:
        _custom(t)


def _clean(t):
    t.c.sudo(f"rm -rf {t.rspec['_path']}")


def _download(t):
    c = t.c
    spec = t.spec
    rspec = t.rspec

    tmp_image_path = f"/tmp/{rspec['name']}.tmp"
    if not os.path.exists(tmp_image_path):
        c.run(f"wget -O {tmp_image_path} {rspec['url']}")

    file_info = c.run(f"file {tmp_image_path}").stdout
    if "XZ compressed data" in file_info:
        c.sudo(f"mv {tmp_image_path} {tmp_image_path}.xz")
        c.sudo(f"xz -d {tmp_image_path}.xz")

    file_info = c.run(f"file {tmp_image_path}").stdout
    os.makedirs(spec["conf"]["vm_images_dir"], exist_ok=True)
    if "QCOW" in file_info:
        c.sudo(f"mv {tmp_image_path} {rspec['_path']}")
    else:
        raise Exception(f"Unsupported image format: {rspec['name']}")


def _custom(t):
    c = t.c
    spec = t.spec
    rspec = t.rspec

    tmp_image_path = f"/tmp/{rspec['name']}.tmp"
    tmp_mount_path = f"/tmp/{rspec['name']}.tmp.mount"
    base_image_path = os.path.join(spec["conf"]["vm_images_dir"], rspec["base"])
    if not os.path.exists(tmp_image_path):
        c.sudo(f"cp {base_image_path} {tmp_image_path}")

    # mount --------------------
    c.sudo("modprobe nbd max_part=63")

    def umount():
        mount = c.run("mount", hide=True).stdout
        if tmp_mount_path in mount:
            c.sudo(f"umount {tmp_mount_path}/dev")
            c.sudo(f"umount {tmp_mount_path}")
            c.sudo("qemu-nbd --disconnect /dev/nbd0")

    umount()
    os.makedirs(tmp_mount_path, exist_ok=True)
    c.sudo(f"qemu-nbd -c /dev/nbd0 {tmp_image_path}")
    c.sudo(f"mount /dev/nbd0p1 {tmp_mount_path}")
    c.sudo(f"mount -o bind /dev {tmp_mount_path}/dev")
    # mount end --------------------

    rspec["_tmp_mount_path"] = tmp_mount_path
    if rspec["base"] == "centos7":
        _custom_common(c, spec, rspec)
        _custom_centos7(c, spec, rspec)
    elif rspec["base"] == "ubuntu20":
        _custom_common(c, spec, rspec)
        _ubuntu_common(c, spec, rspec)
    elif rspec["base"] == "ubuntu22":
        _custom_common(c, spec, rspec)
        _ubuntu_common(c, spec, rspec)

    umount()
    c.sudo(f"cp {tmp_image_path} {rspec['_path']}")
    return


def _custom_common(c, _, rspec):
    root = rspec["_tmp_mount_path"]

    # c.sudo(f"chroot {root} groupadd debugger")
    # c.sudo(f"chroot {root} useradd -g debugger debugger")
    # c.sudo(f"echo 'debugger:debugger' | chroot {root} chpasswd")
    # c.sudo(f"mkdir -p {root}/home/debugger")
    # c.sudo(f"sed -i '$ i %debugger ALL=(ALL) ALL' {root}/etc/sudoers")

    # c.sudo(f"cp /etc/resolv.conf {root}/etc/resolv.conf")
    with open(f"{root}/etc/systemd/system/labo-init.service", "w") as f:
        f.write(
            """
[Unit]
Description=Initial labo-init job
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/labo/bin/labo-init
RemainAfterExit=yes
TimeoutSec=60

# Output needs to appear in instance console output
StandardOutput=journal+console

[Install]
WantedBy=multi-user.target
"""
        )
    os.makedirs(f"{root}/opt/labo/bin", exist_ok=True)

    labo_init = []
    labo_init += [
        """#!/bin/bash
set +x
echo "start labo-init"
"""
    ]

    labo_init += [
        """
function retry() {
    local retries=$1
    shift

    local count=0
    until "$@"; do
        exit=$?
        wait=$((2 ** $count))
        count=$(($count + 1))
        if [ $count -lt $retries ]; then
            echo "Retry $count/$retries exited $exit, retrying in $wait seconds..."
            sleep $wait
        else
            echo "Retry $count/$retries exited $exit, no more retries left."
            return $exit
        fi
    done
    return 0
}
    """
    ]

    labo_init += [
        # cidataをマウントする
        "mkdir -p /mnt/cidata",
        # mount実行時に以下のエラーで追加できない場合がるのでリトライする
        # mount: special device /dev/disk/by-label/cidata does not exist
        "retry 10 mount /dev/disk/by-label/cidata /mnt/cidata",
        # hostnameの設定
        "host=`grep hostname: /mnt/cidata/meta-data | awk '{print $2}'`",
        "hostname $host",
        "echo $host > /etc/hostname",
        'grep "127.0.1.1 $host" /etc/hosts || echo "127.0.1.1 $host" >> /etc/hosts',
        # sshの設定
        "sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config",
        "sudo ssh-keygen -A",
        "systemctl enable ssh",
        "systemctl enable sshd",
        "systemctl restart ssh",
        "systemctl restart sshd",
        # user-dataのスクリプトを開始
        "if [ -e /mnt/cidata/user-data ]; then /bin/bash -Ex /mnt/cidata/user-data; fi",
        # cidateをアンマウントする
        "umount /mnt/cidata",
        "rm -rf /mnt/cidata",
    ]

    with open(f"{root}/opt/labo/bin/labo-init", "w") as f:
        f.write("\n".join(labo_init))
    c.sudo(f"chmod 755 {root}/opt/labo/bin/labo-init")


def _custom_centos7(c, _, rspec):
    root = rspec["_tmp_mount_path"]
    c.sudo(f"chroot {root} systemctl enable labo-init")
    c.sudo(f"chroot {root} yum remove -y cloud-init")
    c.sudo(f"chroot {root} yum install -y dnsmasq tcpdump")
    # selinuxを無効化しておく
    c.sudo(f"sed -i  's/^SELINUX=.*/SELINUX=disabled/g' {root}/etc/selinux/config")
    # 80-net-setup-link.rules があると、udevによって自動でifcfg-eth0を生成してしまうため削除する
    # デフォルトだとdhcpが利用されてしまうため、dhcpがタイムアウトで失敗するまで待たされてしまう
    c.sudo(f"rm -rf {root}/lib/udev/rules.d/80-net-setup-link.rules")
    # network-scripts/ifcfg-eth0(anacondaで作成された?)が残ってるので削除してく
    c.sudo(f"rm -rf {root}/etc/sysconfig/network-scripts/ifcfg-eth0")


def _ubuntu_common(c, _, rspec):
    root = rspec["_tmp_mount_path"]
    c.sudo(f"chroot {root} systemctl enable labo-init")
    c.sudo(f"chroot {root} apt remove -y cloud-init cloud-guest-utils cloud-initramfs-copymods cloud-initramfs-dyn-netconf")
    # 80-net-setup-link.rules があると、udevによって自動でifcfg-eth0を生成してしまうため削除する
    # デフォルトだとdhcpが利用されてしまうため、dhcpがタイムアウトで失敗するまで待たされてしまう
    c.sudo(f"rm -rf {root}/lib/udev/rules.d/80-net-setup-link.rules")
    # network-scripts/ifcfg-eth0(anacondaで作成された?)が残ってるので削除してく
    c.sudo(f"rm -rf {root}/etc/sysconfig/network-scripts/ifcfg-eth0")
    c.sudo(f"mkdir -p {root}/run/systemd/resolve/")
    c.sudo(f"cp /etc/resolv.conf {root}/run/systemd/resolve/stub-resolv.conf")
    c.sudo(f"chroot {root} apt install -y nfs-common")
    c.sudo(f"rm {root}/run/systemd/resolve/stub-resolv.conf")
