import yaml
import os
from lib.spec_utils.complete import update_dict, complete_spec


def load_spec(file):
    spec = {}
    _load_file(spec, file)

    spec["conf"] = _load_conf(spec)
    complete_spec(spec)

    return spec


def _load_file(spec, file):
    with open(file) as f:
        _spec = yaml.safe_load(f)
    for spec_path in _spec.get("imports", []):
        _load_file(_spec, spec_path)

    update_dict(_spec, spec)
    spec.update(_spec)


def _load_conf(spec):
    conf_path = os.environ.get(
        "LABO_CONF",
        os.path.join(
            os.environ.get("XDG_CONFIG_HOME", os.path.join(os.environ.get("HOME", "/tmp"), ".config")),
            "labo.yaml",
        ),
    )

    conf = {
        "domain": f"{spec['common']['namespace']}.example.com",
        "vms_dir": "/opt/labo/vms",
        "vm_images_dir": "/var/nfs/exports/vm_images",
    }

    if os.path.exists(conf_path):
        with open(conf_path) as f:
            tmp_conf = yaml.safe_load(f)
        update_dict(conf, tmp_conf)

    return conf
