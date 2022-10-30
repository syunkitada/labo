import json


def patch_ctx(c):
    def update_docker_ctx(c):
        docker_ps = json.loads("[" + ",".join(c.sudo("docker ps --format='{{json .}}'", hide=True).stdout.splitlines()) + "]")
        docker_ps_map = {}
        for ps in docker_ps:
            docker_ps_map[ps["Names"]] = ps
        c.docker_ps = docker_ps
        c.docker_ps_map = docker_ps_map

    def update_ctx():
        update_docker_ctx(c)

    c.update_ctx = update_ctx
    c.update_docker_ctx = update_docker_ctx
