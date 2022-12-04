import yaml
import os
import ipaddress

MAC_OUI = [0x00, 0x16, 0x3E]


def load_spec(file):
    with open(file) as f:
        tmp_spec = yaml.safe_load(f)

    spec = {}
    for spec_path in tmp_spec.get("imports", []):
        with open(spec_path) as f:
            imported_spec = yaml.safe_load(f)
            spec.update(imported_spec)

    spec.update(tmp_spec)

    complete_spec(spec)
    return spec


def complete_spec(spec):
    spec["conf"] = load_conf(spec)

    template_map = spec.get("template_map", {})

    env_map = {}

    infra_map = {}
    for rspec in spec.get("infras", []):
        if rspec["name"] == "mysql":
            env_map["MYSQL_ROOT_PASSWORD"] = rspec.get("root_password", "rootpass")
            env_map["MYSQL_ADMIN_USER"] = rspec.get("admin_user", "admin")
            env_map["MYSQL_ADMIN_PASSWORD"] = rspec.get("admin_password", "adminpass")
        elif rspec["name"] == "pdns":
            env_map["PDNS_LOCAL_ADDRESS"] = rspec.get("local_address", "127.0.0.1")
            env_map["PDNS_DOMAIN"] = spec["conf"]["domain"]
            for record in rspec.get("records", []):
                record["fqdn"] = record["name"] + "." + spec["conf"]["domain"]

        infra_map[rspec["name"]] = rspec
    spec["_infra_map"] = infra_map
    spec["_env_map"] = env_map

    vm_image_map = spec.get("vm_image_map", {})
    for name, rspec in vm_image_map.items():
        rspec["_name"] = name
        rspec["_path"] = os.path.join(spec["conf"]["vm_images_dir"], name)

    node_map = {}
    links = []
    for i, rspec in enumerate(spec["nodes"]):
        tmp_spec = {}
        for template in rspec.get("templates", []):
            if template not in template_map:
                print(f"template is not found: name={template}, templates={template_map.keys()}")
                exit(1)
            template_spec = template_map[template]
            tmp_spec.update(template_spec)
        tmp_spec.update(rspec)
        rspec.update(tmp_spec)

        _complete_links(i, rspec, rspec.get("links", []))
        links += rspec.get("links", [])
        rspec["_links"] = []

        if rspec["kind"] == "vm":
            vm_dir = os.path.join(spec["conf"]["vms_dir"], rspec["name"])
            rspec["_hostname"] = rspec["name"] + "." + spec["conf"]["domain"]
            rspec["_image"] = vm_image_map[rspec["image"]]
            rspec["_vm_dir"] = vm_dir
            rspec["_image_path"] = os.path.join(vm_dir, "img")
            rspec["_monitor_socket_path"] = os.path.join(vm_dir, "monitor.sock")
            rspec["_serial_socket_path"] = os.path.join(vm_dir, "serial.sock")
            rspec["_serial_log_path"] = os.path.join(vm_dir, "serial.log")
            rspec["_config_image_path"] = os.path.join(vm_dir, "config.img")
            rspec["_metadata_path"] = os.path.join(vm_dir, "meta-data")
            rspec["_userdata_path"] = os.path.join(vm_dir, "user-data")

        node_map[rspec["name"]] = rspec

    spec["_node_map"] = node_map

    for link in links:
        node_map[link["peer"]]["_links"].append(link)

    return


def load_conf(spec):
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
        conf.update(tmp_conf)

    return conf


def _complete_links(i, rspec, links):
    for j, link in enumerate(links):
        _complete_ips(link.get("ips", []))
        _complete_ips(link.get("peer_ips", []))
        link["src_name"] = rspec["name"]
        link["link_name"] = f"{rspec['name']}_{i}_{link['peer']}"
        link["peer_name"] = f"{link['peer']}_{i}_{rspec['name']}"
        if "link_mac" not in link:
            link["link_mac"] = ":".join(map(lambda x: "%02x" % x, MAC_OUI + [i, j, 0]))
        if "peer_mac" not in link:
            link["peer_mac"] = ":".join(map(lambda x: "%02x" % x, MAC_OUI + [i, j, 1]))


def _complete_ips(ips):
    for ip in ips:
        ip_interface = ipaddress.ip_interface(ip["inet"])
        ip["ip"] = str(ip_interface.ip)
        ip["version"] = str(ip_interface.version)
        ip["network"] = str(ip_interface.network)
