太极拳云手/金鸡独立/蹬脚识别

在线（Baidu 人体关键点）与离线（MediaPipe）两种方式：

一、在线识别（Flask + Baidu Body Analysis）
- 设置环境变量（或直接改 `app.py` 占位）：
  - CMD 当前窗口：
    ```cmd
    set BAIDU_API_KEY=你的API_KEY
    set BAIDU_SECRET_KEY=你的SECRET_KEY
    ```
  - 永久（新终端生效）：
    ```cmd
    setx BAIDU_API_KEY "你的API_KEY"
    setx BAIDU_SECRET_KEY "你的SECRET_KEY"
    ```
- 安装并运行：
  ```cmd
  pip install -r requirements.txt
  python app.py
  ```
- 打开 `http://127.0.0.1:5000` 上传动作照片。
- 说明：已使用接口 `rest/2.0/image-classify/v1/body_analysis` 获取关键点并做三类动作判定。

二、离线识别（MediaPipe）
- 将测试图片放为 `test.jpg`，然后运行：
  ```cmd
  python main.py
  ```

备注
- 你提供的“百度文库”的密钥无法用于百度AI人体关键点服务，请到智能云控制台获取对应产品的 API Key/Secret Key。
- 规则阈值仅供参考，需按拍摄角度/距离调优。

