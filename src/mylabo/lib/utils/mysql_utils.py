import configparser

import os
import pymysql
import pymysql.cursors


def get_mysql_connection():
    config = configparser.ConfigParser()
    config.read("/root/container-mysql/.my.cnf")

    conn = pymysql.connect(
        host=config["client"]["host"],
        user=config["client"]["user"],
        password=config["client"]["password"],
        database="pdns",
        cursorclass=pymysql.cursors.DictCursor,
    )

    return conn


def get_pdns_mysql_connection():
    tmp_env_file = os.path.realpath(
        os.path.join(__file__, "../../../../../infra/dns/.env")
    )
    with open(tmp_env_file, "r") as f:
        env_content = f.read()
        for line in env_content.splitlines():
            if line.startswith("MYSQL_SYSTEM_PASSWORD"):
                mysql_system_password = line.split("=")[1]
            elif line.startswith("MYSQL_SYSTEM_USER"):
                mysql_system_user = line.split("=")[1]

    conn = pymysql.connect(
        host="127.0.0.1",
        port=1306,
        user=mysql_system_user,
        password=mysql_system_password,
        database="pdns",
        cursorclass=pymysql.cursors.DictCursor,
    )

    return conn
