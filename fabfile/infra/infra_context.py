from lib import os_utils, infra_utils


class InfraContext:
    def __init__(self, c, spec, debug=False, dryrun=False):
        self.c = c
        self.spec = spec
        self.debug = debug
        self.dryrun = dryrun

    def update(self):
        self.netns_map = os_utils.get_netns_map(self.c)
        self.docker_ps_map = infra_utils.docker.get_docker_ps_map(self.c)
        self.docker_image_map = infra_utils.docker.get_docker_image_map(self.c)
