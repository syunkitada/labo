from mylabo.domain import resource
from mylabo.lib.context import context
from mylabo.lib.runtime import node_context
from mylabo.lib.utils import mysql_utils


class DNSRecord(resource.Resource):
    def __init__(self, ctx: context.Context, manifest: dict):
        self.ctx = ctx
        self.c = node_context.NodeContext(manifest)
        self.manifest = manifest
        self.spec = manifest["spec"]

    def get(self):
        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                select_domain = "SELECT * FROM records"
                cursor.execute(select_domain)
                result = cursor.fetchall()
                print(f"Domain: {result}")

    def apply(self):
        record_name = self.manifest["name"]
        domain_name = self.spec["domain_name"]
        record_type = self.spec["type"].upper()
        record_content = self.spec["content"]

        select_domain = "SELECT * FROM domains WHERE name = %s"
        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                select_records = "SELECT * FROM records WHERE name = %s AND type = %s;"
                cursor.execute(select_records, (record_name, record_type))
                result = cursor.fetchall()
                if len(result) == 0:
                    cursor.execute(select_domain, (domain_name))
                    result = cursor.fetchall()

                    if len(result) == 0:
                        raise Exception("Domain not found")
                    elif len(result) > 2:
                        raise Exception("Domain Conflict")

                    domain_id = list(result)[0]["id"]

                    insert_record = (
                        "INSERT INTO `records` (domain_id,name,type,content,ttl,prio) VALUES"
                        "(%s, %s, %s, %s, '3600', '0');"
                    )
                    cursor.execute(
                        insert_record,
                        (
                            domain_id,
                            record_name,
                            record_type,
                            record_content,
                        ),
                    )
                    print(f"Inserted DNS record {record_name} {record_type} {record_content}")

                elif len(result) == 1:
                    record_id = list(result)[0]["id"]
                    update_record = "UPDATE `records` SET content = %s WHERE id = %s"
                    cursor.execute(
                        update_record,
                        (
                            record_content,
                            record_id,
                        ),
                    )

                    print(f"Updated DNS record {record_name} {record_type} {record_content}")

                else:
                    raise Exception("Conflict DNSRecord")

            conn.commit()

    def delete(self):
        record_name = self.manifest["name"]
        record_type = self.spec["type"]

        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                delete_record = "DELETE FROM records WHERE name = %s AND type = %s"
                cursor.execute(delete_record, (record_name, record_type))

            conn.commit()

    def test(self):
        pass

    def any(self):
        pass
