import os
import yaml
import json
from collections import OrderedDict
from lib.runtime import runtime_context


def check_requrements(c, node_ctxs):
    check_image_requirements(c, node_ctxs)


def check_image_requirements(c, node_ctxs):
    c = runtime_context.new({})

    def get_docker_image_map(c):
        result = c.sudo('docker images --format=\'{"Repository":"{{ .Repository }}","Tag":"{{ .Tag }}"}\'', hide=True).stdout
        docker_images_json = "[" + ",".join(result.splitlines()) + "]"
        docker_images = json.loads(docker_images_json)
        docker_image_map = {}
        for image in docker_images:
            docker_image_map[image["Repository"]] = image

        return docker_image_map


    def get_vm_image_map(c):
        result = c.run('vm-image list', hide=True).stdout
        vm_image_map = {}
        for line in result.splitlines():
            vm_image_map[line] = {}

        return vm_image_map

    docker_image_map = get_docker_image_map(c)
    vm_image_map = get_vm_image_map(c)

    def _get_docker_local_dependencies(image):
        dependencies = []

        index_local = image.find("local/")
        if index_local == -1:
            return dependencies

        image = image[index_local:]
        image = image.split(":")[0]

        dockerfile_path = os.path.join(image.replace("local", "images/docker"), "Dockerfile")
        if os.path.exists(dockerfile_path):
            with open(dockerfile_path) as f:
                for line in f.readlines():
                    if line.find("FROM") == 0:
                        from_image = line.split("FROM")[1].strip()
                        if docker_image_map.get(image) is None:
                            from_dependencies = _get_docker_local_dependencies(from_image)
                            dependencies.append([image, from_dependencies])
                        break
        else:
            raise Exception(f"{image} Dockerfile({dockerfile_path}) is not exists")
        return dependencies

    def _get_vm_local_dependencies(image):
        dependencies = []
        if image.find("local/") != 0:
            return dependencies

        image_yaml_path = os.path.join(image.replace("local", "images/vm"), "image.yaml")
        if os.path.exists(image_yaml_path):
            with open(image_yaml_path) as f:
                spec = yaml.safe_load(f.read())
                if vm_image_map.get(image) is None:
                    from_dependencies = _get_vm_local_dependencies(spec['from'])
                    dependencies.append([image, from_dependencies])
        else:
            raise Exception(f"{image} image.yaml({image_yaml_path}) is not exists")
        return dependencies

    docker_image_dependencies = []
    vm_image_dependencies = []
    for node_ctx in node_ctxs:
        if node_ctx.rspec["kind"] == "container":
            docker_image_dependencies += _get_docker_local_dependencies(node_ctx.rspec["image"])
        elif node_ctx.rspec["kind"] == "vm":
            vm_image_dependencies += _get_vm_local_dependencies(node_ctx.rspec["image"])

    none_docker_images = OrderedDict()
    none_vm_images = OrderedDict()

    def _add_dependencies(dependency, none_images):
        if len(dependency[1]) == 0:
            none_images[dependency[0]] = {}
        else:
            for d in dependency[1]:
                _add_dependencies(d, none_images)
            none_images[dependency[0]] = {}

    for dependency in docker_image_dependencies:
        _add_dependencies(dependency, none_docker_images)
    for dependency in vm_image_dependencies:
        _add_dependencies(dependency, none_vm_images)

    if len(none_docker_images) > 0:
        keys = none_docker_images.keys()
        print(f"You should make local images: {list(keys)}, before this task.")
        print("\nYou should exec following commands.")
        cmds = []
        for none_image in keys:
            image_name = none_image.split("local/")[1]
            cmd = f"docker-image create {image_name}"
            cmds.append(cmd)
            print(f"$ {cmd}")

        user_input = input("\nDo you create images? (yes/no): ")
        if user_input.lower() == "yes":
            for cmd in cmds:
                c.run(cmd)
        else:
            print(user_input)
            exit(0)

    if len(none_vm_images) > 0:
        keys = none_vm_images.keys()
        print(f"You should make local images: {list(keys)}, before this task.")
        print("\nYou should exec following commands.")
        cmds = []
        for none_image in keys:
            image_name = none_image.split("local/")[1]
            cmd = f"vm-image create {image_name}"
            cmds.append(cmd)
            print(f"$ {cmd}")

        user_input = input("\nDo you create images? (yes/no): ")
        if user_input.lower() == "yes":
            for cmd in cmds:
                c.run(cmd)
        else:
            print(user_input)
            exit(0)
