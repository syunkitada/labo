import json


def cmd(nctx):
    if nctx.cmd == "dump":
        print(nctx.rspec)
    elif nctx.cmd == "make":
        make(nctx.c, nctx.rspec)


def make(c, rspec):
    if c.run("ps ax | grep [d]ocker", warn=True).failed:
        c.put("labo/docker/docker.sh", "/tmp/docker.sh")
        c.sudo("/tmp/docker.sh setup")

    if "insecure_docker_registry" in rspec:
        daemon_json = {"insecure-registries": [rspec["insecure_docker_registry"]]}
        c.run(f"echo '{json.dumps(daemon_json)}'> /tmp/daemon.json")
        c.sudo("cp /tmp/daemon.json /etc/docker/daemon.json")
        c.sudo("systemctl restart docker")


def get_docker_ps_map(c):
    docker_ps = json.loads("[" + ",".join(c.sudo("docker ps --format='{{json .}}'", hide=True).stdout.splitlines()) + "]")
    docker_ps_map = {}
    for ps in docker_ps:
        docker_ps_map[ps["Names"]] = ps
    return docker_ps_map


def get_docker_image_map(c):
    result = c.sudo('docker images --format=\'{"Repository":"{{ .Repository }}","Tag":"{{ .Tag }}"}\'', hide=True).stdout
    docker_images_json = "[" + ",".join(result.splitlines()) + "]"
    docker_images = json.loads(docker_images_json)
    docker_image_map = {}
    for image in docker_images:
        docker_image_map[image["Repository"]] = image

    return docker_image_map