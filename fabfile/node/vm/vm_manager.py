import os

import yaml
from lib import colors


def make(nctx):
    if nctx.cmd == "dump":
        print(yaml.safe_dump(nctx.rspec))
    elif nctx.cmd == "make":
        if nctx.next == 0:
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "remake":
        if nctx.next == 0:
            _clean(nctx)
            _make_prepare(nctx)
            nctx.next = 1
        elif nctx.next == 1:
            _make(nctx)
            nctx.next = -1
    elif nctx.cmd == "clean":
        _clean(nctx)
    elif nctx.cmd == "test":
        return _test(nctx)


def _clean(nctx):
    pass


def _test(nctx):
    pass


def _ping(nctx, target):
    pass


def _cmd(nctx, cmd):
    pass


def _make_prepare(nctx):
    pass


def _make(nctx):
    pass
