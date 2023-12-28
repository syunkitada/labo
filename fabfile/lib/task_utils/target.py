import re

def get_re_targets(target):
    re_targets = []
    targets = target.split(",")
    for t in targets:
        re_targets.append(re.compile(t))

    return re_targets

def is_target(rspec, re_targets):
    if len(re_targets) == 0:
        return True
    name = rspec["name"]
    for r in re_targets:
        if r.match(name):
            return True

    print(f"{rspec['name']} is not target")
    return False
