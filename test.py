# 確認 ngrok URL 可以直接訪問圖片
import requests
url = "https://b10eac948396.ngrok-free.app/static/cover.png"
r = requests.get(url)
print(r.status_code)  # 應該是 200
