import configparser

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
