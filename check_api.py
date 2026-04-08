import requests
import time

BAIDU_API_KEY = "CmYFQY5xNqVF58qAR6x0Z2Eb"
BAIDU_SECRET_KEY = "r7lBnYSJyYE8CFYpDgfqDFndZM2J9EgC"

def get_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        'grant_type': 'client_credentials',
        'client_id': BAIDU_API_KEY,
        'client_secret': BAIDU_SECRET_KEY,
    }
    resp = requests.post(url, params=params, timeout=15)
    print("获取Token状态:", resp.status_code)
    print("Token响应:", resp.json())
    return resp.json().get('access_token')

def test_api(token):
    # 测试一个简单请求
    url = f"https://aip.baidubce.com/rest/2.0/image-classify/v1/body_analysis?access_token={token}"
    # 使用一个1x1的透明PNG base64
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    data = {"image": test_image}
    resp = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data, timeout=20)
    print("\nAPI调用状态:", resp.status_code)
    print("API响应:", resp.json())

if __name__ == '__main__':
    print("正在检查百度API状态...\n")
    token = get_token()
    if token:
        print("\n等待5秒后测试API...")
        time.sleep(5)
        test_api(token)
    else:
        print("无法获取Token，请检查密钥")

