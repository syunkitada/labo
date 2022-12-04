import json


def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(rspec)
    elif cmd == "make":
        make(c, spec, rspec)


def make(c, _, rspec):
    if c.run("ps ax | grep [d]ocker", warn=True).failed:
        c.put("labo/docker/docker.sh", "/tmp/docker.sh")
        c.sudo("/tmp/docker.sh setup")

    if "insecure_docker_registry" in rspec:
        daemon_json = {"insecure-registries": [rspec["insecure_docker_registry"]]}
        c.run(f"echo '{json.dumps(daemon_json)}'> /tmp/daemon.json")
        c.sudo("cp /tmp/daemon.json /etc/docker/daemon.json")
        c.sudo("systemctl restart docker")
