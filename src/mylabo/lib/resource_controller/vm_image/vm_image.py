import logging
import os
import re

from mylabo.domain import resource

LOG = logging.getLogger(__name__)


def size_str_to_float(size_str):
    if size_str[-1] == "G":
        return float(size_str[:-1]) * 1024 * 1024 * 1024
    elif size_str[-1] == "M":
        return float(size_str[:-1]) * 1024 * 1024
    elif size_str[-1] == "K":
        return float(size_str[:-1]) * 1024
    return int(size_str)


class VMImage(resource.Resource):
    def __init__(self):
        pass

    def get(self, ctx, spec):
        self._prepare(ctx, spec)

        pass

    def apply(self, ctx, spec):
        self._prepare(ctx, spec)
        _spec = spec["spec"]

        if os.path.exists(spec["_local_vm_image_path"]):
            print(f"Image already exists: {spec['_local_vm_image_path']}")
            return

        if _spec["from"].startswith("https://"):
            self._download(ctx, spec)
        elif _spec["from"].startswith("local/"):
            spec["_local_vm_image_base_path"] = _spec["from"].replace("local/", spec["local_vm_images_dir"] + "/")
            self.customize(ctx, spec)

    def customize(self, ctx, spec):
        tmp_image_path = f"/tmp/{spec['metadata']['name']}.tmp"
        tmp_mount_path = f"/tmp/{spec['metadata']['name']}.tmp.mount"
        tmp_base_image_path = f"/tmp/{spec['metadata']['name']}.base.tmp"

        self._umount(ctx, tmp_mount_path)
        _spec = spec["spec"]

        if "expand" in _spec:
            ctx.sudo(f"cp {spec['_local_vm_image_base_path']} {tmp_base_image_path}")

            result = ctx.sudo(f"virt-filesystems --long --parts --blkdevs -h -a {tmp_base_image_path}")
            device_size = ""
            part_size = 0
            root_part = ""
            for line in result.stdout.splitlines():
                splited_line = re.split(r" +", line)
                if splited_line[0] == "/dev/sda1":
                    tmp_size = size_str_to_float(splited_line[3])
                    if part_size < tmp_size:
                        root_part = splited_line[0]
                        part_size = tmp_size
                elif splited_line[1] == "device":
                    device_size = splited_line[3]

            # パッケージがインストールできるようにサイズを少しだけ拡張する
            size = (size_str_to_float(device_size) + (_spec["expand"]["size"] * 1024 * 1024 * 1024)) / (
                1024 * 1024 * 1024
            )
            size = "{:.1f}G".format(size)

            ctx.sudo(f"qemu-img create -f qcow2 {tmp_image_path} {size}")
            ctx.sudo(f"virt-resize --align-first never --expand {root_part} {tmp_base_image_path} {tmp_image_path}")
        else:
            ctx.sudo(f"cp {spec['_local_vm_image_base_path']} {tmp_image_path}")

        # mount --------------------
        self._mount(ctx, tmp_image_path, tmp_mount_path)

        self.run_steps(ctx, spec, tmp_mount_path)

        if "expand" in spec:
            ctx.sudo(f"chroot {tmp_mount_path} grub-install /dev/nbd0")

        self._umount(ctx, tmp_mount_path)
        ctx.sudo(f"cp {tmp_image_path} {spec['_local_vm_image_path']}")
        return

    def run_steps(self, ctx, spec, mount_path):
        _spec = spec["spec"]

        for step in _spec.get("steps", []):
            print("step", step)
            if "file" in step:
                src_path = os.path.join(spec["_spec_dirpath"], step["file"]["src"])
                if not os.path.exists(src_path):
                    raise Exception(f"src_path is not exists: {src_path}")
                dst = step["file"]["dst"]
                if dst.startswith("/"):
                    dst = dst[1:]
                dst_path = os.path.join(mount_path, dst)
                dst_dir_path = os.path.dirname(dst_path)
                ctx.sudo(f"mkdir -p {dst_dir_path}")
                ctx.sudo(f"cp -r {src_path} {dst_path}")
                if "mode" in step["file"]:
                    ctx.sudo(f"chmod {str(step['file']['mode'])} {dst_path}")
            elif "cmd" in step:
                ctx.sudo(f"chroot {mount_path} sh -xec '{step['cmd']}'")

    def _umount(self, ctx, mount_path: str):
        ctx.sudo(f"umount {mount_path}/dev", warn=True, hide=True)
        ctx.sudo(f"umount {mount_path}/proc", warn=True, hide=True)
        ctx.sudo(f"umount {mount_path}/sys", warn=True, hide=True)
        ctx.sudo(f"umount {mount_path}", warn=True, hide=True)
        ctx.sudo("qemu-nbd --disconnect /dev/nbd0", warn=True, hide=True)
        print(f"umount {mount_path}")

    def _mount(self, ctx, image_path, mount_path: str):
        ctx.sudo("modprobe nbd max_part=63")
        self._umount(ctx, mount_path)
        os.makedirs(mount_path, exist_ok=True)
        ctx.sudo(f"qemu-nbd -c /dev/nbd0 {image_path}")

        result = ctx.sudo("/sbin/fdisk -l -u /dev/nbd0")
        linux_filesystem_device = ""
        for line in result.stdout.splitlines():
            if re.match(".* Linux root .*", line):
                splited_line = re.split(r" +", line)
                linux_filesystem_device = splited_line[0]
                break

        if linux_filesystem_device == "":
            raise Exception("linux_filesystem_device is not found")

        ctx.sudo(f"mount {linux_filesystem_device} {mount_path}")
        ctx.sudo(f"mount -o bind /dev {mount_path}/dev")
        ctx.sudo(f"mount -o bind /proc {mount_path}/proc")
        ctx.sudo(f"mount -o bind /sys {mount_path}/sys")
        print(f"image_path={image_path}")
        print(f"mount_path={mount_path}")

    def delete(self, ctx, spec):
        self._prepare(ctx, spec)
        pass

    def _prepare(self, ctx, spec):
        vm_images_dir = spec["local_vm_images_dir"]
        if not os.path.exists(vm_images_dir):
            os.makedirs(vm_images_dir)
            LOG.info("vm_images_dir created", extra={"metadata": {"dir": vm_images_dir}})
        else:
            LOG.debug("vm_images_dir already exists", extra={"metadata": {"dir": vm_images_dir}})

        spec["_local_vm_image_path"] = os.path.join(spec["local_vm_images_dir"], spec["metadata"]["name"])

    def _download(self, ctx, spec):
        image_name = spec["metadata"]["name"]
        image_from = spec["spec"]["from"]

        tmp_image_path = f"/tmp/{image_name}.tmp"
        if not os.path.exists(tmp_image_path):
            result = ctx.sudo(f"wget -O {tmp_image_path} {image_from}", warn=True)
            if result.failed:
                os.remove(tmp_image_path)
                raise Exception(f"Failed to wget: {image_from}")

        result = ctx.sudo(f"file {tmp_image_path}")
        file_info = result.stdout
        if "XZ compressed data" in file_info:
            ctx.sudo(f"mv {tmp_image_path} {tmp_image_path}.xz")
            ctx.sudo(f"xz -d {tmp_image_path}.xz")
            result = ctx.sudo(f"file {tmp_image_path}")
            file_info = result.stdout

        if "QCOW" in file_info:
            ctx.sudo(f"cp {tmp_image_path} {spec['_local_vm_image_path']}")
            ctx.sudo(f"rm {tmp_image_path}")
        else:
            raise Exception(f"Unsupported image format: {file_info}")
