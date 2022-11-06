def make(c, spec, rspec):
    c.run("mysql -e 'CREATE DATABASE IF NOT EXISTS pdns'")

    resolver_name = rspec["name"] + "-pdns"
    recursor_name = rspec["name"] + "-pdns-recursor"
    if resolver_name not in c.docker_ps_map:
        c.sudo(
            """
        docker run -d --rm --network host --name {0}
            -e PDNS_local_address=127.0.0.1
            -e PDNS_local_port=8053
            -e PDNS_master=yes
            -e PDNS_default_ttl=1500
            -e PDNS_gmysql_host=127.0.0.1
            -e PDNS_gmysql_port=3306
            -e PDNS_gmysql_user=admin
            -e PDNS_gmysql_password=adminpass
            -e PDNS_gmysql_dbname=pdns
            pschiffe/pdns-mysql
        """.format(
                resolver_name
            )
        )

    if recursor_name not in c.docker_ps_map:
        c.sudo(
            " ".join(
                [
                    f"docker run -d --rm --network host --name {recursor_name}",
                    f"-e PDNS_local_address={rspec['ns']}",
                    "-e PDNS_forward_zones_recurse=.=8.8.8.8",
                    "-e PDNS_forward_zones=example.com=127.0.0.1:8053",
                    f"-e PDNS_forward_zones={spec['conf']['domain']}=127.0.0.1:8053",
                    "pschiffe/pdns-recursor",
                ]
            )
        )

    domain_id = get_domain_id_with_create(c, spec)
    domain_records = [
        {"fqdn": spec["conf"]["domain"], "type": "SOA", "content": "ns1.example.com admin.example.com 2021071818 10800 1800 604800 86400"},
        {"fqdn": spec["conf"]["domain"], "type": "NS", "content": rspec["ns"]},
    ]
    records = domain_records + rspec.get("records", [])

    record_map = get_record_map(c, domain_id)
    for record in records:
        if record["fqdn"] not in record_map:
            create_record(c, domain_id, record)


def get_domain_id_with_create(c, spec):
    cmd = f"mysql pdns -e \"SELECT id, name FROM domains WHERE name = '{spec['conf']['domain']}'\" | grep '{spec['conf']['domain']}'"
    result = c.run(cmd, warn=True)
    if result.failed:
        c.run(f"mysql pdns -e \"INSERT INTO domains (name, type) VALUES('{spec['conf']['domain']}', 'NATIVE')\"")
        result = c.run(cmd)

    return result.stdout.split()[0]


def get_record_map(c, domain_id):
    result = c.run(f'mysql pdns -e "SELECT name FROM records WHERE domain_id = {domain_id}"')
    record_map = {}
    for line in result.stdout.splitlines()[1:]:
        record_map[line.split()[0]] = {}
    return record_map


def create_record(c, domain_id, record):
    c.run(
        'mysql pdns -e "INSERT INTO records (domain_id, name, type, content, ttl, prio) '
        + f"VALUES({domain_id}, '{record['fqdn']}', '{record['type'].upper()}', '{record['content']}', '3600', '0')\""
    )
