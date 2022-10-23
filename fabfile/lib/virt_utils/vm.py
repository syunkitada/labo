# qemu utils

import os


def make_image(_, spec, infra_map):
    nfs = infra_map[spec["nfs"]]
    image_path = os.path.join(nfs["path"], spec["name"] + ".img")
    print(image_path)
    # TODO


def make_vm(_, spec):
    print("debug spec", spec)
    # TODO
