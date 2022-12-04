def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(rspec)
    elif cmd == "make":
        make(c, spec, rspec)


def make(c, spec, rspec):
    if c.run("ps ax | grep [m]ysqld", warn=True).failed or True:
        c.sudo("labo/pdns/pdns.sh")
        c.sudo(f"labo/pdns/domain.sh create {spec['conf']['domain']} {rspec['local_address']}")
        record_map = get_record_map(c, spec["conf"]["domain"])
        for record in rspec.get("records", []):
            if record["fqdn"] not in record_map:
                create_record(c, spec["conf"]["domain"], record)


def get_record_map(c, domain):
    result = c.sudo(f"labo/pdns/record.sh list {domain}")
    record_map = {}
    for line in result.stdout.splitlines()[1:]:
        record_map[line.split()[0]] = {}
    return record_map


def create_record(c, domain, record):
    c.sudo(f"labo/pdns/record.sh create {domain} {record['fqdn']} {record['type'].upper()} {record['content']}")
