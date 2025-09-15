from mylabo.lib.utils import dict_utils


def apply(spec: dict):
    if "spec_modifications" not in spec:
        return

    for spec_modification in spec["spec_modifications"]:
        if "overwrite_node" in spec_modification:
            if "nodes" not in spec["spec"]:
                raise Exception("nodes is not found in spec")

            for node in spec["spec"]["nodes"]:
                if node["name"] in spec_modification["overwrite_node"]:
                    node_modification = spec_modification["overwrite_node"][node["name"]]

                    if "extend_steps" in node_modification:
                        node["spec"]["steps"].extend(node_modification["extend_steps"])
                        del node_modification["extend_steps"]

                    dict_utils.update_dict(node, node_modification)

        elif "extend_nodes" in spec_modification:
            if "nodes" not in spec["spec"]:
                raise Exception("nodes is not found in spec")

            spec["spec"]["nodes"].extend(spec_modification["extend_nodes"])

    del spec["spec_modifications"]
