import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose


def angle(a, b, c):
    """Compute angle ABC in degrees, with B as the vertex."""
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    ba = a - b
    bc = c - b
    nba = np.linalg.norm(ba)
    nbc = np.linalg.norm(bc)
    if nba == 0 or nbc == 0:
        return None
    cos_angle = np.dot(ba, bc) / (nba * nbc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def check_jin_ji_du_li(landmarks):
    # Left-leg support example: right ankle higher than left knee; arms level
    left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]
    right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y]
    left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
    right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
    left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]
    right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]

    is_lift = (right_ankle[1] < left_knee[1]) or (left_ankle[1] < right_knee[1])
    is_balance = abs(right_wrist[1] - left_wrist[1]) < 0.1 and abs(right_wrist[0] - left_wrist[0]) > 0.2
    if is_lift and is_balance:
        return True, "金鸡独立动作规范"
    if is_lift:
        return False, "手臂平衡有待加强"
    return False, "未检测到金鸡独立或动作不规范"


def check_yun_shou(landmarks):
    left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]
    right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]
    left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
    right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
    wrist_diff = abs(left_wrist[1] - right_wrist[1])
    if wrist_diff < 0.06 and left_wrist[1] < left_shoulder[1] - 0.1 and right_wrist[1] < right_shoulder[1] - 0.1:
        return True, "云手动作规范"
    return False, "未检测到云手动作或动作不规范"


def check_deng_jiao(landmarks):
    left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]
    right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y]
    left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
    right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
    if left_ankle[1] < right_knee[1]:
        return True, "蹬脚（左）动作规范"
    if right_ankle[1] < left_knee[1]:
        return True, "蹬脚（右）动作规范"
    return False, "未检测到蹬脚动作或动作不规范"


def analyze_pose_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return "无法读取图片: " + str(image_path)
    with mp_pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5) as pose:
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            return "未检测到人体关键点"
        landmarks = results.pose_landmarks.landmark
        jinji, jinji_msg = check_jin_ji_du_li(landmarks)
        yunshou, yunshou_msg = check_yun_shou(landmarks)
        dengjiao, dengjiao_msg = check_deng_jiao(landmarks)
        return "\n".join([jinji_msg, yunshou_msg, dengjiao_msg])


if __name__ == "__main__":
    img_path = "test.jpg"  # Replace with your image path
    result = analyze_pose_image(img_path)
    print(result)


