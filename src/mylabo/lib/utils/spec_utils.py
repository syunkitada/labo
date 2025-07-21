from os.path import abspath, dirname

import yaml

from . import dict_utils


def load_specs(file) -> list[dict]:
    specs = _load_file(file)

    for spec in specs:
        dict_utils.complete_template(spec)
        dict_utils.complete_data(spec)

    return specs


def _load_file(file) -> list[dict]:
    specs = []
    namespace = file.rsplit("/", 1)[1].split(".", 1)[0].replace("_", "-")

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
        if "namespace" not in spec:
            spec["namespace"] = namespace
        spec["_spec_filepath"] = spec_filepath
        spec["_spec_dirpath"] = spec_dirpath
        spec["_script_dir"] = "/tmp/mylabo/namespace/"  # TODO make this configurable
        specs.append(spec)

    return specs
