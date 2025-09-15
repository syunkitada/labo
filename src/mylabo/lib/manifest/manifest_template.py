import copy
from mylabo.lib.utils import dict_utils


def complete(manifest: dict):
    _complete_recursively(manifest, manifest)

    if "template_map" in manifest:
        del manifest["template_map"]


def _complete_recursively(root_manifest: dict, data: dict | list):
    if isinstance(data, dict):
        _apply_template(root_manifest, data)

        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                data[k] = _complete_recursively(root_manifest, v)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            if isinstance(v, dict) or isinstance(v, list):
                data[i] = _complete_recursively(root_manifest, v)

    return data


def _apply_template(root_manifest: dict, data: dict):
    if "templates" not in data:
        return data

    if "template_map" not in root_manifest:
        raise Exception("template_map is not found in root_manifest")

    template_map = root_manifest["template_map"]
    tmp_data = {}

    for template in data["templates"]:
        if template not in template_map:
            raise Exception(f"template {template} is not found in template_map")

        template = copy.deepcopy(template_map[template])

        dict_utils.update_dict(tmp_data, template)

    dict_utils.update_dict(tmp_data, data)
    data.update(tmp_data)
