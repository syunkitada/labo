import datetime

from mylabo.lib.context import context
from mylabo.lib.runtime import node_context
from mylabo.domain import resource
from mylabo.lib.utils import mysql_utils


class DNSDomain(resource.Resource):
    def __init__(self, ctx: context.Context, manifest: dict):
        self.ctx = ctx
        self.c = node_context.NodeContext(manifest)
        self.manifest = manifest
        self.spec = manifest["spec"]

    def apply(self):
        domain_name = self.manifest["name"]
        domain_ns = self.spec["ns"]

        now = datetime.datetime.now()
        soa_content = "ns1.example.com admin.example.com " + now.strftime("%Y%m%d%H") + " 10800 1800 604800 86400"

        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                select_domain = "SELECT * FROM domains WHERE name = %s"
                cursor.execute(select_domain, (domain_name))
                result = cursor.fetchall()

                if len(result) == 0:
                    insert_domain = (
                        "INSERT INTO domains (name, master, last_check, type, notified_serial, account)"
                        " VALUES (%s, NULL, NULL, 'NATIVE', NULL, NULL);"
                    )
                    cursor.execute(insert_domain, (domain_name))
                    print(f"Inserted DNS domain {domain_name}")

                    cursor.execute(select_domain, (domain_name))
                    result = cursor.fetchall()
                elif len(result) == 1:
                    print(f"Domain already exists: {domain_name}")
                elif len(result) > 2:
                    raise Exception("Conflict DNSDomain")

                domain_id = list(result)[0]["id"]

                select_records = "SELECT * FROM records WHERE name = %s;"
                cursor.execute(select_records, (domain_name))
                result = cursor.fetchall()
                if len(result) == 0:
                    insert_record = (
                        "INSERT INTO `records` (domain_id,name,type,content,ttl,prio) VALUES"
                        "(%s, %s, 'SOA', %s, '3600', '0'),"
                        "(%s, %s, 'NS', %s, '3600', '0');"
                    )
                    cursor.execute(
                        insert_record,
                        (
                            domain_id,
                            domain_name,
                            soa_content,
                            domain_id,
                            domain_name,
                            domain_ns,
                        ),
                    )
                    print(f"Inserted DNS records for {domain_name}")
                else:
                    print(f"DNS records already exist for: {domain_name}")

            conn.commit()

    def delete(self):
        domain_name = self.manifest["name"]

        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                select_domain = "DELETE FROM domains WHERE name = %s"
                cursor.execute(select_domain, (domain_name))

                select_domain = "DELETE FROM records WHERE name = %s"
                cursor.execute(select_domain, (domain_name))

            conn.commit()

    def get(self):
        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                select_domain = "SELECT * FROM domains"
                cursor.execute(select_domain)
                result = cursor.fetchall()
                print(f"Domain: {result}")

    def test(self):
        pass

    def any(self):
        pass
