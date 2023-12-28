from lib.runtime import runtime_context


class NodeContext:
    def __init__(self, spec, cmd, rspec, debug, dryrun, ictx=None):
        self.c = runtime_context.new(spec)
        self.cmd = cmd
        self.spec = spec
        self.rspec = rspec
        self.next = 0
        self.debug = debug
        self.dryrun = dryrun
        self.rc = None
        self.ictx = ictx
