import os
import base64
import json
from typing import Dict, Optional, Tuple
import requests
from flask import Flask, request, render_template, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "taiji-2025-secret-key")
# 百度AI密钥（已配置，可直接使用）
BAIDU_API_KEY = "CmYFQY5xNqVF58qAR6x0Z2Eb"
BAIDU_SECRET_KEY = "r7lBnYSJyYE8CFYpDgfqDFndZM2J9EgC"
TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
# 修复原错误接口：改为百度人体关键点识别正确接口
BODY_ANALYSIS_URL = "https://aip.baidubce.com/rest/2.0/image-classify/v1/body_analysis"
# 图片限制（符合要求文档）
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp'}

# 检查文件后缀
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 获取百度AI Token
def get_access_token() -> Optional[str]:
    try:
        params = {
            "grant_type": "client_credentials",
            "client_id": BAIDU_API_KEY,
            "client_secret": BAIDU_SECRET_KEY,
        }
        resp = requests.post(TOKEN_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        flash(f"获取Token失败：{str(e)[:50]}")
        return None

# 调用百度人体分析API
def call_baidu_body_analysis(image_base64: str) -> Dict:
    access_token = get_access_token()
    if not access_token:
        return {"error": "Token获取失败，请检查网络或API密钥"}
    url = f"{BODY_ANALYSIS_URL}?access_token={access_token}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"image": image_base64}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=20)
        return resp.json()
    except Exception as e:
        return {"error": f"API调用失败：{str(e)[:50]}"}

# 关键点提取与计算辅助函数
Point = Optional[Tuple[float, float]]
def _get_point(parts: Dict, name: str) -> Point:
    p = parts.get(name)
    if not p or p.get("x") is None or p.get("y") is None:
        return None
    return float(p["x"]), float(p["y"])
def _angle(a: Point, b: Point, c: Point) -> Optional[float]:
    if not all([a, b, c]):
        return None
    import math
    ba = (a[0]-b[0], a[1]-b[1])
    bc = (c[0]-b[0], c[1]-b[1])
    nba, nbc = math.hypot(*ba), math.hypot(*bc)
    if nba == 0 or nbc == 0:
        return None
    cosang = (ba[0]*bc[0] + ba[1]*bc[1]) / (nba*nbc)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosang))))

# 太极动作判定（金鸡独立/云手/蹬脚）
def check_jinji(parts: Dict) -> Tuple[bool, str]:
    left_ankle, right_ankle = _get_point(parts, "left_ankle"), _get_point(parts, "right_ankle")
    left_knee, right_knee = _get_point(parts, "left_knee"), _get_point(parts, "right_knee")
    if not all([left_ankle, right_ankle, left_knee, right_knee]):
        return False, "❌ 关键点不足，无法判定"
    if left_ankle[1] < right_knee[1]:
        return True, "✅ 金鸡独立（右腿支撑）动作规范"
    if right_ankle[1] < left_knee[1]:
        return True, "✅ 金鸡独立（左腿支撑）动作规范"
    return False, "❌ 未检测到金鸡独立（双脚未抬起）"

def check_yunshou(parts: Dict) -> Tuple[bool, str]:
    left_wrist, right_wrist = _get_point(parts, "left_wrist"), _get_point(parts, "right_wrist")
    left_shoulder, right_shoulder = _get_point(parts, "left_shoulder"), _get_point(parts, "right_shoulder")
    if not all([left_wrist, right_wrist, left_shoulder, right_shoulder]):
        return False, "❌ 关键点不足，无法判定"
    avg_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
    avg_wrist_y = (left_wrist[1] + right_wrist[1]) / 2
    if avg_wrist_y <= avg_shoulder_y + 50:
        return True, "✅ 云手动作规范（双手抬起）"
    return False, "❌ 未检测到云手（双手位置偏低）"

def check_dengjiao(parts: Dict) -> Tuple[bool, str]:
    left_ankle, right_ankle = _get_point(parts, "left_ankle"), _get_point(parts, "right_ankle")
    left_knee, right_knee = _get_point(parts, "left_knee"), _get_point(parts, "right_knee")
    if not all([left_ankle, right_ankle, left_knee, right_knee]):
        return False, "❌ 关键点不足，无法判定"
    if left_ankle[1] < right_knee[1]:
        lift = int(right_knee[1] - left_ankle[1])
        return True, f"✅ 蹬脚（左）动作规范（抬高{lift}px）"
    if right_ankle[1] < left_knee[1]:
        lift = int(left_knee[1] - right_ankle[1])
        return True, f"✅ 蹬脚（右）动作规范（抬高{lift}px）"
    return False, "❌ 未检测到蹬脚（双脚未明显抬高）"

# 分析百度API返回结果，生成动作反馈
def analyze_actions_from_baidu(result: Dict) -> Dict:
    if "error_msg" in result:
        return {"整体提示": f"API错误：{result['error_msg']}（错误码{result.get('error_code')}）"}
    if "error" in result:
        return {"整体提示": result["error"]}
    person_info = result.get("person_info", [])
    if not person_info:
        return {"整体提示": "❌ 未检测到人体，请检查图片"}
    parts = person_info[0].get("body_parts", {})
    return {
        "金鸡独立": check_jinji(parts)[1],
        "云手": check_yunshou(parts)[1],
        "蹬脚": check_dengjiao(parts)[1]
    }

# 主路由：上传+分析
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # 检查文件是否存在
        if "file" not in request.files:
            flash("❌ 请选择要上传的图片")
            return redirect(url_for("upload_file"))
        file = request.files["file"]
        if file.filename == "":
            flash("❌ 文件名不能为空")
            return redirect(url_for("upload_file"))
        # 检查文件格式和大小
        if file and allowed_file(file.filename):
            file_data = file.read()
            if len(file_data) > MAX_FILE_SIZE:
                flash("❌ 图片大小超过4MB，请压缩后上传")
                return redirect(url_for("upload_file"))
            # 转换为base64并调用API
            image_b64 = base64.b64encode(file_data).decode("utf-8")
            raw_result = call_baidu_body_analysis(image_b64)
            # 处理API调用次数上限
            if raw_result.get("error_code") == 18:
                action_feedback = {
                    "整体提示": "⚠️ 百度API调用次数达上限",
                    "解决方案": "1. 等待1-2分钟重试 2. 使用离线版：python main.py"
                }
            else:
                action_feedback = analyze_actions_from_baidu(raw_result)
            return render_template("result.html", result=raw_result, actions=action_feedback)
        else:
            flash(f"❌ 不支持的文件格式，仅支持{ALLOWED_EXTENSIONS}")
            return redirect(url_for("upload_file"))
    # GET请求：返回上传页
    return render_template("upload.html")

if __name__ == "__main__":
    # 允许局域网访问，方便手机/其他设备测试
    app.run(host="0.0.0.0", port=5000, debug=True)