#!/usr/bin/env python3

import subprocess
import yaml
import os
import argparse
p = argparse.ArgumentParser()
p.add_argument('action', choices=[
    'create', 'recreate',
    'list', 'delete',
    'mount', 'umount',
], help='action')
p.add_argument('image_name', help='image name', nargs='*', default=[])
args = p.parse_args()


IMAGE_ROOT = '/mnt/nfs/vm_images/'

VM_IMAGE_DIR = os.path.join(os.path.dirname(__file__), '../../images/vm')

def main():
    if args.action == "list":
        print("list")
    else:
        if len(args.image_name) == 0:
            p.error(f"{args.action} require image_name")
        name = args.image_name[0]
        spec = new_spec(name)

        if args.action == "create":
            create(spec)
        elif args.action == "delete":
            delete(spec)
        elif args.action == "recreate":
            delete(spec)
            create(spec)
        elif args.action == "mount":
            mount(spec, spec["_image_path"])
        elif args.action == "unmount":
            umount(spec)


def delete(spec):
    if os.path.exists(spec["_image_path"]):
        subprocess.run(["rm", "-rf", spec["_image_path"]])

def create(spec):
    os.makedirs(VM_IMAGE_DIR, exist_ok=True)

    if os.path.exists(spec["_image_path"]):
        return

    if spec['from'].startswith('https://'):
        download(spec)
        spec['_base_image_path'] = ''
    elif spec['from'].startswith('local/'):
        spec['_base_image_path'] = spec['from'].replace('local/', IMAGE_ROOT)
    custom(spec)


def download(spec):
    tmp_image_path = f"/tmp/{spec['_name']}.tmp"
    if not os.path.exists(tmp_image_path):
        subprocess.run(["wget", "-O", tmp_image_path, spec['base']['url']])

    result = subprocess.run(["file", tmp_image_path], capture_output=True)
    file_info = result.stdout.decode('utf-8')
    if 'XZ compressed data' in file_info:
        subprocess.run(["mv", tmp_image_path, f"{spec['_tmp_image_path']}.xz"])
        subprocess.run(["xz", "-d", f"{spec['_tmp_image_path']}.xz"])

    result = subprocess.run(["file", tmp_image_path], capture_output=True)
    file_info = result.stdout.decode('utf-8')
    if "QCOW" in file_info:
        subprocess.run(['mv', tmp_image_path, spec['_image_path']])
    else:
        raise Exception(f"Unsupported image format: {spec['_name']}")


def new_spec(name):
    image_src_dir = os.path.join(VM_IMAGE_DIR, name)
    image_src_yaml = os.path.join(image_src_dir, 'image.yaml')
    spec = {}
    if not os.path.exists(image_src_yaml):
        print(f"{image_src_yaml} is not exists")
        exit(1)
    with open(image_src_yaml) as f:
        spec = yaml.safe_load(f)

    spec["_name"] = name
    spec["_tmp_image_path"] = f"/tmp/{name}.tmp"
    spec["_tmp_mount_path"] = f"/tmp/{name}.tmp.mount"
    spec["_image_path"] = os.path.join(IMAGE_ROOT, name)
    spec["_image_src_dir"] = image_src_dir

    return spec


def mount(spec, image_path):
    subprocess.run(["modprobe", "nbd", "max_part=63"])
    umount(spec)
    os.makedirs(spec["_tmp_mount_path"], exist_ok=True)
    subprocess.run(["qemu-nbd", "-c", "/dev/nbd0", image_path])
    subprocess.run(["mount", "/dev/nbd0p1", spec["_tmp_mount_path"]])
    subprocess.run(["mount", "-o", "bind", "/dev", f"{spec['_tmp_mount_path']}/dev"])
    print(f"image_path={image_path}")
    print(f"mount_path={spec['_tmp_mount_path']}")


def umount(spec):
    result = subprocess.run(["mount"], capture_output=True)
    result = result.stdout.decode('utf-8')
    if spec['_tmp_mount_path'] in result:
        subprocess.run(["umount", f"{spec['_tmp_mount_path']}/dev"])
        subprocess.run(["umount", spec['_tmp_mount_path']])
        subprocess.run(["qemu-nbd", "--disconnect", "/dev/nbd0"])
    print(f"umount {spec['_tmp_mount_path']}")


def custom(spec):
    tmp_image_path = f"/tmp/{spec['_name']}.tmp"
    tmp_mount_path = f"/tmp/{spec['_name']}.tmp.mount"
    spec['_root_dir'] = tmp_mount_path

    subprocess.run(["cp", spec['_base_image_path'], tmp_image_path])

    # mount --------------------
    mount(spec, spec["_tmp_image_path"])

    print("debug custom")
    try:
        run_steps(spec)
    except Exception as e:
        print(f"Failed run_steps: {e}")

    umount(spec)
    subprocess.run(["cp", tmp_image_path, spec['_image_path']])
    return

def run_steps(spec):
    for step in spec.get("steps", []):
        print("step", step)
        if 'file' in step:
            src_path = os.path.join(spec['_image_src_dir'], step['file']['src'])
            if not os.path.exists(src_path):
                raise Exception(f"src_path is not exists: {src_path}")
            dst = step['file']['dst']
            if dst.startswith("/"):
                dst = dst[1:]
            dst_path = os.path.join(spec['_tmp_mount_path'], dst)
            dst_dir_path = os.path.dirname(dst_path)
            subprocess.run(["mkdir", "-p", dst_dir_path])
            subprocess.run(["cp", src_path, dst_path])
            print("debug cp", src_path, dst_path)
            subprocess.run(["chmod", str(step['file']['mod']), dst_path])
        elif 'cmd' in step:
            subprocess.run(["chroot", spec['_tmp_mount_path'], "bash", "-xec", step['cmd']])


if __name__ == "__main__":
    main()
