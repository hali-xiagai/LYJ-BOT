import sys
import json, os
import configparser
import re
import random, datetime
import time
import typing
import songs as song_module

from flask import Flask, request, abort, render_template, Response, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest,
    ImagemapArea,
    ImagemapAction,
    ImagemapMessage,
    ImagemapBaseSize,
    ImagemapExternalLink,
    ImagemapVideo,
    MessageImagemapAction,
    URIImagemapAction,
)


#Config Parser
# config = configparser.ConfigParser()
# config.read('config.ini')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

#config
#channel_access_token=config['Line']['CHANNEL_ACCESS_TOKEN']
#channel_secret=config['Line']['CHANNEL_SECRET']
#liff_id_everyday_song=config['Line']['LIFF_EVERYDAY_SONG_CHANNEL_ID']
#BASE_URL=config['Sever']['ROOT_URL']

#env
channel_access_token=os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret=os.getenv("CHANNEL_SECRET")
liff_id_everyday_song=os.getenv("LIFF_EVERYDAY_SONG_CHANNEL_ID")
liff_id_add_song=os.getenv("LIFF_ADD_SONG_CHANNEL_ID")
admin_token=os.getenv("ADMIN_TOKEN")
BASE_URL=os.getenv("ROOT_URL")

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)
with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

# 假設 liff_url 是你的 LIFF 網頁
liff_url = "https://liff.line.me/" + liff_id_everyday_song

@app.route("/", methods=["POST"])
def home():
    # 從 POST body 拿 token
    token = request.form.get("token")

    print("Received token:", token)
    if token != admin_token:
        return jsonify({"error": "Unauthorized"}), 403
    return "Sever is running."

@app.route("/everyday_song")
def everyday_song():
    with open("today_song.json", "r", encoding="utf-8") as f:
        song = json.load(f)
    return render_template("everyday_song.html", song=song, liff_url=liff_id_everyday_song)

@app.route("/video_watched", methods=["POST"])
def video_watched():
    data = request.get_json()
    user_id = data.get("userId")
    user_name = data.get("userName")
    video_id = data.get("videoId")
    # 可以把觀看紀錄存到檔案或資料庫
    print(f"使用者{user_name}看完影片 {video_id}")
    
    message = f"感謝你聽完今天的推薦歌曲！"
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)]
        )
    )
    return jsonify({"status": "ok"})


@app.route('/song', methods=['GET'])
def song_form():

    return render_template('add_song.html', liff_id=liff_id_add_song)

@app.route("/add_song", methods=["POST"])
def add_song_submit():
    data = request.get_json()
    user_id = data.get("userId")
    title = data.get("title")
    artist = data.get("artist")
    genre = data.get("genre")
    url = data.get("url")
    year = data.get("year")

    url = extract_youtube_id(url)
    if not url:
        result = {
            "status": "url_error",
            "message": "請輸入正確的 YouTube 連結！"
        }
        return Response(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json"
        )
        #return jsonify({"status": "error", "message": "請輸入正確的 YouTube 連結！"})

    # 載入目前歌單
    if os.path.exists("songs.json"):
        with open("songs.json", "r", encoding="utf-8") as f:
            songs = json.load(f)
    else:
        songs = []

    for song in songs:
        if song["title"] == title and song["artist"] == artist or song["url"] == url:
            result = {
                "status": "error",
                "message": f"歌曲 {request.json.get('title')}已存在！"
            }
            return Response(
                json.dumps(result, ensure_ascii=False),
                mimetype="application/json"
            )
            #return jsonify({"status": "error", "message": f"歌曲 '{title}' 已存在！"})
        
    # 新增一首歌
    id = max([s['id'] for s in songs], default=0) + 1
    new_song = {
        "id": id,
        "title": title,
        "artist": artist,
        "year": year,
        "genre": genre,
        "url": url
    }
    songs.append(new_song)

    # 寫回檔案
    with open("songs.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    result = {
        "status": "ok",
        "message": f"成功加入 {request.json.get('title')}！"
    }
    message = f"您推薦的歌曲 {title} 已成功加入歌單，感謝您的貢獻！"
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)]
        )
    )
    print("✅ 新增歌曲回傳：", result)  # ← 加這行確認有進來
    return Response(
        json.dumps(result, ensure_ascii=False),
        mimetype="application/json"
    )
    #return jsonify({"status": "ok", "message": f"成功加入 {title}！"})
def extract_youtube_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

# ===== userId 資料檔 =====
USER_FILE = 'user_ids.json'

def load_user_ids():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return []

def save_user_ids(user_ids):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_ids, f, ensure_ascii=False, indent=2)

@app.route("/choose_daily_song", methods=["POST"])
def choose_daily_song():
    token = request.form.get("token")
    print("Received token:", token)
    if token != admin_token:
        return jsonify({"error": "Unauthorized"}), 403
    
    songs = song_module.load_songs()
    if not songs:
        return None
    today = datetime.date.today().isoformat()
    random.seed(time.time_ns())
    song = random.choice(songs)
    song["date"] = today  # 記錄生成日期
    with open("today_song.json", "w", encoding="utf-8") as f:
        json.dump(song, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.datetime.now()}] 更新今日歌曲：{song['title']} - {song['artist']}")
    return "Daily song updated"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'
    
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    print(f"👋 使用者加入好友：{user_id}")
    
    user_ids = load_user_ids()
    if user_id not in user_ids:
        user_ids.append(user_id)
        save_user_ids(user_ids)

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    print(f"收到訊息的 userId 是：{user_id}")
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
    if user_id == ADMIN_USER_ID:
        if event.message.text.strip() == "1":
            songs = song_module.load_songs()
            if not songs:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="目前沒有任何歌曲喔！")]
                    )
                )
                return
            song_list = "\n".join([f"{song['id']}. {song['title']} - {song['artist']}" for song in songs])
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"目前所有歌曲如下：\n{song_list}")]
                )
            )
        if event.message.text.strip() == "2":
            with open("today_song.json", "r", encoding="utf-8") as f:
                song = json.load(f)
            imagemap_message = set_message(song)
            text_message = TextMessage(
            text=f"{song['date']}推薦歌曲：{song['title']} - {song['artist']}")
            line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[text_message, imagemap_message]
                        )
                    )
        else:
            text = '選單:\n1. 查看所有歌曲\n2. 今日歌曲'
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
            
@app.route("/send_daily_message", methods=["POST"])
def send_daily_message():
    token = request.form.get("token")
    print("Received token:", token)
    if token != admin_token:
        return jsonify({"error": "Unauthorized"}), 403
    
    user_ids = load_user_ids()
    with open("today_song.json", "r", encoding="utf-8") as f:
        song = json.load(f)   
    imagemap_message = set_message(song)
    text_message = TextMessage(
    text=f"🎶 今日推薦歌曲：{song['title']} - {song['artist']} 暖你一整天")
    #print(imagemap_message)
    #print(song)
    for uid in user_ids:
        line_bot_api.push_message(
            PushMessageRequest(
            to=uid, 
            messages=[text_message, imagemap_message]  # 直接放 Message object
        ))
    print(f"✅ 今日推薦歌曲：{song['title']} - {song['artist']}已推播給使用者")
    return "Daily message sent"

def set_message(song):
    image_base_url = BASE_URL + "/static/imagemap"  # 替換成你的圖片網址
    image_base_url = image_base_url.replace("http://", "https://")

    imagemap_message = ImagemapMessage(
    base_url=image_base_url,
    alt_text=f"🎶 今日推薦歌曲：{song['title']} - {song['artist']} 暖你一整天",
    base_size=ImagemapBaseSize(width=1040, height=1040),
    actions=[
        URIImagemapAction(
            type = "uri",
            link_uri=liff_url,
            area=ImagemapArea(x=0, y=0, width=1040, height=1040)
        )
    ]
)
    return imagemap_message

if __name__ == "__main__":
    app.run(port=5001)
    