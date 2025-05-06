from os.path import abspath, dirname

import yaml

from . import dict_utils


def load_specs(file) -> list[dict]:
    specs = _load_file(file)

    for spec in specs:
        dict_utils.complete_data(spec, spec)

    return specs


def _load_file(file) -> list[dict]:
    specs = []

    spec_filepath = abspath(file)
    spec_dirpath = dirname(spec_filepath)
    with open(spec_filepath) as f:
        readed = f.read()
        splited_txt = readed.split("---")

    for txt in splited_txt:
        spec = {}
        _spec = yaml.safe_load(txt)

        for spec_path in _spec.get("imports", []):
            imported_specs = _load_file(spec_path)
            for imported_spec in imported_specs:
                dict_utils.update_dict(spec, imported_spec)

        spec.update(_spec)
        spec["_spec_filepath"] = spec_filepath
        spec["_spec_dirpath"] = spec_dirpath
        specs.append(spec)

    return specs


# def _load_conf(spec, file):
#     conf_path = os.environ.get(
#         "LABO_CONF",
#         os.path.join(
#             os.environ.get("XDG_CONFIG_HOME", os.path.join(os.environ.get("HOME", "/tmp"), ".config")),
#             "labo.yaml",
#         ),
#     )
#
#     if "common" not in spec:
#         spec["common"] = {}
#
#     if "namespace" not in spec["common"]:
#         namespace = file.rsplit("/", 1)[1].split(".", 1)[0].replace("_", "-")
#         spec["_meta"] = {"spec_file": file}
#         spec["common"]["namespace"] = namespace
#
#     if "nfs_path" not in spec["common"]:
#         spec["common"]["nfs_path"] = "/mnt/nfs"
#
#     conf = {
#         "domain": f"{spec['common']['namespace']}.example.com",
#         "vms_dir": "/opt/labo/vms",
#         "vm_images_dir": "/var/nfs/exports/vm_images",
#     }
#
#     if os.path.exists(conf_path):
#         with open(conf_path) as f:
#             tmp_conf = yaml.safe_load(f)
#         update_dict(conf, tmp_conf)
#
#     return conf
