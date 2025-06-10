import os
import sys
import time
import subprocess
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

if len(sys.argv) < 2:
    print("Usage: python3 record.py <twitch_username>")
    sys.exit(1)

TWITCH_USERNAME = sys.argv[1]

# 環境変数
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

_token_info = {
    "access_token": None,
    "expire_time": datetime.min,
}

def get_access_token():
    now = datetime.utcnow()
    if _token_info["access_token"] and now < _token_info["expire_time"]:
        return _token_info["access_token"]

    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        data = response.json()
        _token_info["access_token"] = data["access_token"]
        # 有効期限の5分前に期限切れ扱いとする（バッファ）
        _token_info["expire_time"] = now + timedelta(seconds=data["expires_in"] - 300)
        return _token_info["access_token"]
    except Exception as e:
        print("トークン取得に失敗しました:", e)
        return None

def is_live(username):
    access_token = get_access_token()
    if not access_token:
        return False

    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return len(resp.json().get("data", [])) > 0
    except Exception as e:
        print("配信状態の確認に失敗しました:", e)
        return False

def record_and_upload(username):
    ts_file = f"{username}_{time.strftime('%Y%m%d_%H%M%S')}.ts"
    mp4_file = ts_file.replace(".ts", ".mp4")
    zip_file = mp4_file + ".zip"

    subprocess.run([
        "streamlink", "--twitch-disable-ads",
        f"https://www.twitch.tv/{username}", "best", "-o", ts_file
    ], check=True)

    subprocess.run(["ffmpeg", "-i", ts_file, "-c", "copy", mp4_file], check=True)
    os.remove(ts_file)

    s3_path = f"s3://{AWS_BUCKET_NAME}/{TWITCH_USERNAME}/{mp4_file}"
    subprocess.run(["aws", "s3", "cp", mp4_file, s3_path], check=True)
    os.remove(mp4_file)

def main():
    while True:
        if is_live(TWITCH_USERNAME):
            print(f"{TWITCH_USERNAME} の配信を検出、録画を開始します...")
            record_and_upload(TWITCH_USERNAME)
        else:
            print(f"{TWITCH_USERNAME} はまだ配信していません。")
        time.sleep(60)

if __name__ == "__main__":
    main()
