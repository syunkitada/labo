import yaml
import os

from invoke.config import Config


def load_spec(file):
    with open(file) as f:
        spec = yaml.safe_load(f)

    complete_spec(spec)
    return spec


def complete_spec(spec):
    template_map = {}
    for rspec in spec["templates"]:
        template_map[rspec["name"]] = rspec

    infra_map = {}
    for rspec in spec["infras"]:
        infra_map[rspec["name"]] = rspec
    spec["_infra_map"] = infra_map

    spec["conf"] = load_conf(spec)

    vm_image_map = {}
    for rspec in spec["vm_images"]:
        rspec["_path"] = os.path.join(spec["conf"]["vm_images_dir"], rspec["name"])
        vm_image_map[rspec["name"]] = rspec
    spec["_vm_image_map"] = vm_image_map

    node_map = {}
    for rspec in spec["nodes"]:
        tmp_spec = {}
        for template in rspec.get("templates", []):
            template_spec = template_map[template]
            tmp_spec.update(template_spec)
        tmp_spec.update(rspec)
        rspec.update(tmp_spec)
        node_map[rspec["name"]] = rspec
    spec["_node_map"] = node_map

    return


def load_conf(spec):
    conf_path = os.environ.get(
        "LABO_CONF",
        os.path.join(
            os.environ.get("XDG_CONFIG_HOME", os.path.join(os.environ.get("HOME", "/tmp"), ".config")),
            "labo.yaml",
        ),
    )

    nfs_path = spec["_infra_map"]["nfs"]["path"]
    conf = {
        "vm_images_dir": os.path.join(nfs_path, "vm_images"),
    }

    if os.path.exists(conf_path):
        with open(conf_path) as f:
            tmp_conf = yaml.safe_load(f)
        conf.update(tmp_conf)

    return conf
