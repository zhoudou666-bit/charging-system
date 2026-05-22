from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_conn
import random
import datetime

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)


def cancel_expired_reservations():
    """
    自动取消超时预约：
    已预约状态下，如果预约创建后 5 分钟内没有产生该充电桩的充电数据，
    则自动把预约状态改为“已取消”。
    """
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reservation r
        SET r.status = '已取消'
        WHERE r.status = '已预约'
          AND TIMESTAMPDIFF(MINUTE, r.create_time, NOW()) >= 5
          AND NOT EXISTS (
              SELECT 1
              FROM charging_data d
              WHERE d.pile_id = r.pile_id
                AND d.create_time >= r.create_time
                AND d.create_time <= DATE_ADD(r.create_time, INTERVAL 5 MINUTE)
          )
    """)

    conn.commit()
    affected = cursor.rowcount

    cursor.close()
    conn.close()

    return affected


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
    # 每次查询充电桩时，先自动取消超时预约
    cancel_expired_reservations()

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
    # 每次刷新统计卡片时，先自动取消超时预约
    cancel_expired_reservations()

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
    点击“查看实时数据”后，会插入一条 charging_data。
    如果该充电桩存在“已预约”记录，则认为用户已经开始充电，
    将预约状态改为“已充电”。
    """
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

    # 插入充电数据
    cursor.execute(
        """
        INSERT INTO charging_data(pile_id, voltage, current_value, power, warning_status)
        VALUES(%s, %s, %s, %s, %s)
        """,
        (pile_id, voltage, current_value, power, warning_status)
    )

    # 如果该充电桩有未超时的预约，则标记为已充电
    cursor.execute(
        """
        UPDATE reservation
        SET status = '已充电'
        WHERE pile_id = %s
          AND status = '已预约'
          AND TIMESTAMPDIFF(MINUTE, create_time, NOW()) < 5
        """,
        (pile_id,)
    )

    # 如果电流异常，生成预警
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
        "message": "实时数据获取成功",
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
    # 新增预约前，先清理已经超时的旧预约
    cancel_expired_reservations()

    data = request.json

    user_id = data.get("user_id")
    pile_id = data.get("pile_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not user_id or not pile_id or not start_time or not end_time:
        return jsonify({
            "code": 400,
            "message": "预约参数不完整"
        })

    conn = get_conn()
    cursor = conn.cursor()

    # 检查该充电桩是否已经有未完成预约
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
        "message": "预约成功，请在 5 分钟内开始充电，否则系统将自动取消预约"
    })


@app.route("/api/reservation/list", methods=["GET"])
def reservation_list():
    # 查询预约记录前，自动取消超时预约
    cancel_expired_reservations()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            r.id,
            r.user_id,
            r.pile_id,
            p.pile_name,
            p.location,
            r.start_time,
            r.end_time,
            r.status,
            r.create_time
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