from os.path import abspath

import os
import yaml

from mylabo.lib.utils import dict_utils
from mylabo.lib.manifest import (
    manifest_data,
    manifest_template,
    manifest_nodes,
    manifest_spec_modifications,
    manifest_data,
)


def load_manifests(file: str) -> list[dict]:
    """Load and process manifests from file or directory."""
    manifests = _load_file(file)

    for manifest in manifests:
        manifest["_referer"] = {}
        init_manifest(manifest, file)
        manifest_spec_modifications.apply(manifest)
        manifest_template.complete(manifest)
        manifest_nodes.complete(manifest)
        manifest_data.complete(manifest, 0)
        manifest_data.complete(manifest, 1)

    return manifests


def _load_file(file: str) -> list[dict]:
    manifests = []

    manifest_filepath = abspath(file)
    if not os.path.exists(manifest_filepath):
        raise Exception(f"Manifest file not found: {manifest_filepath}")

    if os.path.isdir(manifest_filepath):
        files = os.listdir(manifest_filepath)
        for file in files:
            manifests.extend(_load_file(os.path.join(manifest_filepath, file)))
        return manifests

    splited_txt = []
    with open(manifest_filepath) as f:
        tmp_lines = []
        for line in f.readlines():
            if line.strip().startswith("#"):
                continue
            if line.strip() == "---":
                splited_txt.append("".join(tmp_lines))
                tmp_lines = []
                continue
            tmp_lines.append(line)
        splited_txt.append("".join(tmp_lines))

    for txt in splited_txt:
        manifest = {}
        _manifest = yaml.safe_load(txt)

        for manifest_path in _manifest.get("imports", []):
            imported_manifests = _load_file(manifest_path)
            for imported_manifest in imported_manifests:
                dict_utils.update_dict(manifest, imported_manifest)

        dict_utils.update_dict(manifest, _manifest)
        if "extend_spec_modifications" in manifest:
            if "spec_modifications" not in manifest:
                manifest["spec_modifications"] = []
            manifest["spec_modifications"].extend(manifest["extend_spec_modifications"])
            del manifest["extend_spec_modifications"]

        manifests.append(manifest)

    return manifests


def init_manifest(manifest: dict, file: str):
    manifest_dir = os.path.dirname(os.path.realpath(file))

    namespace = file.rsplit("/", 1)[1].split(".", 1)[0].replace("_", "-")
    if "namespace" not in manifest:
        manifest["namespace"] = namespace

    manifest["_script_dir"] = os.path.join(
        manifest["local_namespaces_dir"], manifest["kind"].lower(), manifest["namespace"]
    )

    manifest["_manifest_dir"] = manifest_dir
