import requests
import re
import os
import time
import threading
from datetime import datetime
from flask import Flask, jsonify


# ===== 設定 =====

USERS = [
    "mable_siriwalee",
    "piployrr",
    "pangjiewrr",
    "aangelinaa.ss",
    "ppammelar"
]

CHECK_INTERVAL = 60

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1479037672402976781/67D4iNmtrHObr2XI6_BMJgCTvub8sVqWPZX_QbJN8yi4YQLEyVdmr0aEAUxbxyV-n8xl"

# =================

headers = {
    "User-Agent": "Mozilla/5.0"
}

status_data = {}
last_status = {}

app = Flask(__name__)


def get_room_id(username):

    url = f"https://www.tiktok.com/@{username}"
    r = requests.get(url, headers=headers)

    match = re.search(r'"roomId":"(\d+)"', r.text)

    if match:
        return match.group(1)

    return None


def check_live(room_id):

    api = "https://www.tiktok.com/api/live/detail/"

    params = {
        "aid": "1988",
        "roomID": room_id
    }

    r = requests.get(api, headers=headers, params=params)
    data = r.json()

    status = data.get("LiveRoomInfo", {}).get("status")

    return status == 2


def send_discord(username, live):

    if live:

        message = {
            "embeds": [
                {
                    "title": "🔴 TikTok 開播",
                    "description": f"{username} 正在直播",
                    "url": f"https://www.tiktok.com/@{username}/live",
                    "color": 16711680
                }
            ]
        }

    else:

        message = {
            "content": f"⚫ {username} 已下播"
        }

    requests.post(DISCORD_WEBHOOK, json=message)


def monitor():
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        for username in USERS:
            try:
                room_id = get_room_id(username)
                #print(room_id)

                if not room_id:
                    live = False
                else:
                    live = check_live(room_id)

                status_data[username] = {"live": live, "room_id": room_id}

                # 終端機輸出
                icon = "🔴" if live else "⚫"
                print(f"[{now}] {username} {icon} {'LIVE' if live else 'OFFLINE'}, flush=True")

                # Discord 通知只在狀態改變時發送
                if username not in last_status:
                    last_status[username] = live

                if live and not last_status[username]:
                    send_discord(username, True)
                if not live and last_status[username]:
                    send_discord(username, False)

                last_status[username] = live

            except Exception as e:
                print(f"[{now}] error: {username} {e}")

        time.sleep(CHECK_INTERVAL)


@app.route("/api/live")
def api_live():
    return jsonify(status_data)


threading.Thread(target=monitor, daemon=True).start()

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




