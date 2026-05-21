import os
import pymysql

def get_conn():
    return pymysql.connect(
        host=os.getenv("MYSQLHOST", "localhost"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER", "root"),
        password=os.getenv("MYSQLPASSWORD", "123456"),
        database=os.getenv("MYSQLDATABASE", "charging_system"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )