from os.path import abspath

import yaml

from . import dict_utils


def load_specs(file) -> list[dict]:
    specs = _load_file(file)

    for spec in specs:
        spec["_referer"] = {}
        dict_utils.init_spec(spec, file)
        dict_utils.modify_spec(spec)
        dict_utils.complete_template(spec)
        dict_utils.complete_nodes(spec)
        dict_utils.complete_data(spec)
        dict_utils.must_complete_data(spec)

    return specs


def _load_file(file) -> list[dict]:
    specs = []

    spec_filepath = abspath(file)
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

        dict_utils.update_dict(spec, _spec)
        if "extend_spec_modifications" in spec:
            if "spec_modifications" not in spec:
                spec["spec_modifications"] = []
            spec["spec_modifications"].extend(spec["extend_spec_modifications"])
            del spec["extend_spec_modifications"]

        specs.append(spec)

    return specs
