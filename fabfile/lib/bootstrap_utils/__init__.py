import json


def init(c, spec):
    daemon_json = {"insecure-registries": [spec["common"]["insecure_docker_registry"]]}
    if c.run("ps ax | grep [d]ocker", warn=True).failed:
        c.put("docker/docker.sh", "/tmp/docker.sh")
        c.sudo("/tmp/docker.sh setup")
    c.run(f"echo '{json.dumps(daemon_json)}'> /tmp/daemon.json")
    c.sudo("cp /tmp/daemon.json /etc/docker/daemon.json")
    c.sudo("systemctl restart docker")
