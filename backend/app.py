from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_conn
import random
import datetime
import os

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)


def get_beijing_now():
    """
    获取北京时间。
    Railway 服务器默认可能是 UTC 时间，所以统一使用 UTC+8。
    """
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def format_datetime(value):
    """
    Python 后端统一格式化时间，避免 jsonify 把 datetime 转成 GMT 字符串。
    """
    if value is None:
        return None

    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def complete_expired_reservations():
    """
    预约到期后自动确认充电：
    如果当前北京时间已经超过预约到期时间 end_time，
    并且预约状态仍为“已预约”，则自动生成一条正常充电记录，
    并将预约状态改为“已充电”。

    同时更新 charging_pile 表中的电压、电流、功率和更新时间，
    让充电桩状态监测页面能看到最新更新时间。
    """
    conn = get_conn()
    cursor = conn.cursor()

    now = get_beijing_now()

    cursor.execute("""
        SELECT 
            id,
            pile_id
        FROM reservation
        WHERE status = '已预约'
          AND end_time <= %s
    """, (now,))

    expired_list = cursor.fetchall()

    for item in expired_list:
        reservation_id = item["id"]
        pile_id = item["pile_id"]

        voltage = round(random.uniform(215, 225), 2)
        current_value = round(random.uniform(2, 5), 2)
        power = round(voltage * current_value / 1000, 2)
        warning_status = "正常"

        cursor.execute(
            """
            INSERT INTO charging_data(
                pile_id, voltage, current_value, power, warning_status, create_time
            )
            VALUES(%s, %s, %s, %s, %s, %s)
            """,
            (pile_id, voltage, current_value, power, warning_status, now)
        )

        cursor.execute(
            """
            UPDATE charging_pile
            SET 
                voltage = %s,
                current_value = %s,
                power = %s,
                update_time = %s
            WHERE id = %s
            """,
            (voltage, current_value, power, now, pile_id)
        )

        cursor.execute(
            """
            UPDATE reservation
            SET status = '已充电'
            WHERE id = %s
            """,
            (reservation_id,)
        )

    conn.commit()

    cursor.close()
    conn.close()

    return len(expired_list)


@app.route("/")
def index():
    return "校园电动车充电监测 + AI安全预警系统后端启动成功"


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json

    username = data.get("username")
    password = data.get("password")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM app_user WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": user
        })

    return jsonify({
        "code": 401,
        "message": "账号或密码错误"
    })


@app.route("/api/pile/list", methods=["GET"])
def pile_list():
    complete_expired_reservations()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id,
            pile_name,
            location,
            status,
            voltage,
            current_value,
            power,
            DATE_FORMAT(update_time, '%Y-%m-%d %H:%i:%s') AS update_time
        FROM charging_pile
        ORDER BY id ASC
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": data
    })


@app.route("/api/stats", methods=["GET"])
def stats():
    complete_expired_reservations()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM charging_pile")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS free_count FROM charging_pile WHERE status='空闲'")
    free_count = cursor.fetchone()["free_count"]

    cursor.execute("SELECT COUNT(*) AS used_count FROM charging_pile WHERE status='占用'")
    used_count = cursor.fetchone()["used_count"]

    cursor.execute("SELECT COUNT(*) AS fault_count FROM charging_pile WHERE status='故障'")
    fault_count = cursor.fetchone()["fault_count"]

    cursor.execute("SELECT COUNT(*) AS warning_count FROM warning_log")
    warning_count = cursor.fetchone()["warning_count"]

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "data": {
            "total": total,
            "free_count": free_count,
            "used_count": used_count,
            "fault_count": fault_count,
            "warning_count": warning_count
        }
    })


@app.route("/api/pile/simulate/<int:pile_id>", methods=["GET"])
def simulate_data(pile_id):
    """
    模拟充电数据：
    点击“查看实时数据”后，插入一条 charging_data；
    同时更新 charging_pile 表中的电压、电流、功率和更新时间；
    如果该充电桩存在“已预约”记录，则认为用户已经开始充电，
    将预约状态改为“已充电”。
    """
    complete_expired_reservations()

    now = get_beijing_now()

    voltage = round(random.uniform(215, 225), 2)
    current_value = round(random.uniform(1, 9), 2)
    power = round(voltage * current_value / 1000, 2)

    warning_status = "正常"

    if current_value >= 8:
        warning_status = "严重过载"
    elif current_value >= 6:
        warning_status = "疑似过载"

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO charging_data(
            pile_id, voltage, current_value, power, warning_status, create_time
        )
        VALUES(%s, %s, %s, %s, %s, %s)
        """,
        (pile_id, voltage, current_value, power, warning_status, now)
    )

    cursor.execute(
        """
        UPDATE charging_pile
        SET 
            voltage = %s,
            current_value = %s,
            power = %s,
            update_time = %s
        WHERE id = %s
        """,
        (voltage, current_value, power, now, pile_id)
    )

    cursor.execute(
        """
        UPDATE reservation
        SET status = '已充电'
        WHERE pile_id = %s
          AND status = '已预约'
        """,
        (pile_id,)
    )

    if warning_status != "正常":
        warning_level = "严重" if warning_status == "严重过载" else "一般"

        cursor.execute(
            """
            INSERT INTO warning_log(
                warning_type, warning_level, description, status, create_time
            )
            VALUES(%s, %s, %s, '未处理', %s)
            """,
            (
                "过载充电",
                warning_level,
                f"{pile_id}号充电桩电流异常，当前电流为{current_value}A，存在{warning_status}风险",
                now
            )
        )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "实时数据获取成功",
        "data": {
            "pile_id": pile_id,
            "voltage": voltage,
            "current_value": current_value,
            "power": power,
            "warning_status": warning_status,
            "create_time": format_datetime(now)
        }
    })


@app.route("/api/charging-data/list", methods=["GET"])
def charging_data_list():
    complete_expired_reservations()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            d.id,
            d.pile_id,
            p.pile_name,
            p.location,
            d.voltage,
            d.current_value,
            d.power,
            d.warning_status,
            DATE_FORMAT(d.create_time, '%Y-%m-%d %H:%i:%s') AS create_time
        FROM charging_data d
        LEFT JOIN charging_pile p ON d.pile_id = p.id
        ORDER BY d.create_time DESC
    """)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "data": data
    })


@app.route("/api/reservation/add", methods=["POST"])
def add_reservation():
    complete_expired_reservations()

    data = request.json

    user_id = data.get("user_id")
    pile_id = data.get("pile_id")

    if not user_id or not pile_id:
        return jsonify({
            "code": 400,
            "message": "预约参数不完整"
        })

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM reservation
        WHERE pile_id = %s
          AND status = '已预约'
        LIMIT 1
    """, (pile_id,))

    existed = cursor.fetchone()

    if existed:
        cursor.close()
        conn.close()
        return jsonify({
            "code": 400,
            "message": "该充电桩当前已有预约，请选择其他充电桩"
        })

    now = get_beijing_now()
    end_time = now + datetime.timedelta(minutes=5)

    cursor.execute(
        """
        INSERT INTO reservation(
            user_id, pile_id, start_time, end_time, status, create_time
        )
        VALUES(%s, %s, %s, %s, '已预约', %s)
        """,
        (user_id, pile_id, now, end_time, now)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "预约成功，预约有效期为 5 分钟，到期后系统将自动确认充电并生成充电记录"
    })


@app.route("/api/reservation/list", methods=["GET"])
def reservation_list():
    complete_expired_reservations()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            r.id,
            r.user_id,
            r.pile_id,
            p.pile_name,
            p.location,
            DATE_FORMAT(r.start_time, '%Y-%m-%d %H:%i:%s') AS start_time,
            DATE_FORMAT(r.end_time, '%Y-%m-%d %H:%i:%s') AS end_time,
            DATE_FORMAT(r.create_time, '%Y-%m-%d %H:%i:%s') AS create_time,
            r.status
        FROM reservation r
        LEFT JOIN charging_pile p ON r.pile_id = p.id
        ORDER BY r.create_time DESC
    """)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "预约记录获取成功",
        "data": data
    })


@app.route("/api/reservation/delete/<int:reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):
    data = request.json or {}
    user_role = data.get("role")

    if user_role != "admin":
        return jsonify({
            "code": 403,
            "message": "无权限删除预约记录"
        })

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM reservation WHERE id = %s",
        (reservation_id,)
    )

    conn.commit()
    affected = cursor.rowcount

    cursor.close()
    conn.close()

    if affected > 0:
        return jsonify({
            "code": 200,
            "message": "预约记录删除成功"
        })

    return jsonify({
        "code": 404,
        "message": "预约记录不存在"
    })


@app.route("/api/charging-data/delete/<int:data_id>", methods=["DELETE"])
def delete_charging_data(data_id):
    data = request.json or {}
    user_role = data.get("role")

    if user_role != "admin":
        return jsonify({
            "code": 403,
            "message": "无权限删除充电数据记录"
        })

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM charging_data WHERE id = %s",
        (data_id,)
    )

    conn.commit()
    affected = cursor.rowcount

    cursor.close()
    conn.close()

    if affected > 0:
        return jsonify({
            "code": 200,
            "message": "充电数据记录删除成功"
        })

    return jsonify({
        "code": 404,
        "message": "充电数据记录不存在"
    })


@app.route("/api/warning/list", methods=["GET"])
def warning_list():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id,
            warning_type,
            warning_level,
            description,
            status,
            image_path,
            DATE_FORMAT(create_time, '%Y-%m-%d %H:%i:%s') AS create_time
        FROM warning_log
        ORDER BY create_time DESC
    """)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "data": data
    })


@app.route("/api/warning/handle/<int:warning_id>", methods=["POST"])
def handle_warning(warning_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE warning_log SET status='已处理' WHERE id=%s",
        (warning_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "处理成功"
    })


@app.route("/api/warning/delete/<int:warning_id>", methods=["DELETE"])
def delete_warning(warning_id):
    data = request.json or {}
    user_role = data.get("role")

    if user_role != "admin":
        return jsonify({
            "code": 403,
            "message": "无权限删除预警记录"
        })

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM warning_log WHERE id = %s",
        (warning_id,)
    )

    conn.commit()
    affected = cursor.rowcount

    cursor.close()
    conn.close()

    if affected > 0:
        return jsonify({
            "code": 200,
            "message": "预警记录删除成功"
        })

    return jsonify({
        "code": 404,
        "message": "预警记录不存在"
    })


@app.route("/api/ai/mock-detect", methods=["POST"])
def mock_ai_detect():
    data = request.json
    now = get_beijing_now()

    warning_type = data.get("warning_type", "电动车进宿舍")
    warning_level = data.get("warning_level", "严重")
    description = data.get("description", f"AI智能体识别到违规行为：{warning_type}")
    suggestion = data.get("suggestion", "建议管理员及时核查并处理。")

    full_description = description + " 处置建议：" + suggestion

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO warning_log(
            warning_type, warning_level, description, status, create_time
        )
        VALUES(%s, %s, %s, '未处理', %s)
        """,
        (
            warning_type,
            warning_level,
            full_description,
            now
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "AI智能体分析完成，已生成预警",
        "data": {
            "warning_type": warning_type,
            "warning_level": warning_level,
            "description": description,
            "suggestion": suggestion,
            "create_time": format_datetime(now)
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)