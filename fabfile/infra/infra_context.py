from lib import os_utils
from . import modules


class InfraContext:
    def __init__(self, c, spec, debug=False, dryrun=False):
        self.c = c
        self.spec = spec
        self.debug = debug
        self.dryrun = dryrun

    def update(self):
        self.netns_map = os_utils.get_netns_map(self.c)
        self.docker_ps_map = modules.docker.get_docker_ps_map(self.c)
        self.docker_image_map = modules.docker.get_docker_image_map(self.c)
