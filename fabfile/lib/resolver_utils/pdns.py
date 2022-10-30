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
            """
            docker run -d --rm --network host --name {0}
            -e PDNS_forward_zones_recurse=.=8.8.8.8
            -e PDNS_forward_zones=example.com=127.0.0.1:8053
            pschiffe/pdns-recursor
            """.format(
                recursor_name
            )
        )
