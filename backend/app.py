from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_conn
import random

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)


@app.route("/")
def index():
    return "校园电动车充电监测 + AI安全预警系统后端启动成功"


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    print("收到登录请求：", data)

    username = data.get("username")
    password = data.get("password")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM app_user WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()

    print("查询到的用户：", user)

    cursor.close()
    conn.close()

    if user:
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": user
        })
    else:
        return jsonify({
            "code": 401,
            "message": "账号或密码错误"
        })


@app.route("/api/pile/list", methods=["GET"])
def pile_list():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM charging_pile")
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
        INSERT INTO charging_data(pile_id, voltage, current_value, power, warning_status)
        VALUES(%s, %s, %s, %s, %s)
        """,
        (pile_id, voltage, current_value, power, warning_status)
    )

    if warning_status != "正常":
        cursor.execute(
            """
            INSERT INTO warning_log(warning_type, warning_level, description, status)
            VALUES(%s, %s, %s, '未处理')
            """,
            (
                "过载充电",
                "严重" if warning_status == "严重过载" else "一般",
                f"{pile_id}号充电桩电流异常，当前电流为{current_value}A，存在{warning_status}风险"
            )
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "data": {
            "pile_id": pile_id,
            "voltage": voltage,
            "current_value": current_value,
            "power": power,
            "warning_status": warning_status
        }
    })

@app.route("/api/charging-data/list", methods=["GET"])
def charging_data_list():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.*, p.pile_name, p.location
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
    data = request.json

    user_id = data.get("user_id")
    pile_id = data.get("pile_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reservation(user_id, pile_id, start_time, end_time, status)
        VALUES(%s, %s, %s, %s, '已预约')
        """,
        (user_id, pile_id, start_time, end_time)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "message": "预约成功"
    })


@app.route("/api/warning/list", methods=["GET"])
def warning_list():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM warning_log ORDER BY create_time DESC")
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


@app.route("/api/ai/mock-detect", methods=["POST"])
def mock_ai_detect():
    data = request.json

    warning_type = data.get("warning_type", "电动车进宿舍")
    warning_level = data.get("warning_level", "严重")
    description = data.get("description", f"AI智能体识别到违规行为：{warning_type}")
    suggestion = data.get("suggestion", "建议管理员及时核查并处理。")

    full_description = description + " 处置建议：" + suggestion

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO warning_log(warning_type, warning_level, description, status)
        VALUES(%s, %s, %s, '未处理')
        """,
        (
            warning_type,
            warning_level,
            full_description
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
            "suggestion": suggestion
        }
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)