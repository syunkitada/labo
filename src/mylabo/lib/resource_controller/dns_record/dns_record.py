from mylabo.domain import resource
from mylabo.lib.utils import mysql_utils


class DNSRecord(resource.Resource):
    def __init__(self):
        pass

    def get(self, ctx, spec):
        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                select_domain = "SELECT * FROM records"
                cursor.execute(select_domain)
                result = cursor.fetchall()
                print(f"Domain: {result}")

    def apply(self, ctx, spec: dict):
        record_name = spec["metadata"]["name"]
        domain_name = spec["spec"]["domain_name"]
        record_type = spec["spec"]["type"].upper()
        record_content = spec["spec"]["content"]

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

                else:
                    raise Exception("Conflict DNSRecord")

            conn.commit()

    def delete(self, ctx, spec):
        record_name = spec["metadata"]["name"]
        record_type = spec["spec"]["type"]

        conn = mysql_utils.get_mysql_connection()
        with conn:
            with conn.cursor() as cursor:
                delete_record = "DELETE FROM records WHERE name = %s AND type = %s"
                cursor.execute(delete_record, (record_name, record_type))

            conn.commit()
