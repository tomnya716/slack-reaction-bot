from flask import Flask, request, jsonify
import os
import re
import tempfile
import threading
from slack_sdk import WebClient
import pandas as pd

app = Flask(__name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

def parse_slack_url(url):
    pattern = r"/archives/([A-Z0-9]+)/p(\d{16})"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("SlackメッセージURLが不正です")
    channel_id = match.group(1)
    raw_ts = match.group(2)
    return channel_id, f"{raw_ts[:-6]}.{raw_ts[-6:]}"

def generate_reaction_report(channel_id, message_ts, requested_by_user_id=None):
    members = client.conversations_members(channel=channel_id)["members"]
    users = {}
    for uid in members:
        info = client.users_info(user=uid)
        if not info["user"]["is_bot"] and not info["user"]["deleted"]:
            users[uid] = info["user"]["real_name"]

    message = client.reactions_get(channel=channel_id, timestamp=message_ts)["message"]
    reactions = message.get("reactions", [])
    reaction_names = [r["name"] for r in reactions]

    data = []
    for uid, name in users.items():
        row = {"ユーザー名": name}
        for r in reaction_names:
            row[r] = 0
        data.append(row)

    for r in reactions:
        for uid in r["users"]:
            uname = users.get(uid)
            if uname:
                for row in data:
                    if row["ユーザー名"] == uname:
                        row[r["name"]] = 1

    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df.to_excel(tmp.name, index=False)
        tmp_path = tmp.name

    client.files_upload(
        channels=channel_id,
        file=tmp_path,
        title="リアクション集計",
        filename="reaction_report.xlsx",
        initial_comment=f"<@{requested_by_user_id}> 集計結果です 📊" if requested_by_user_id else "📊 リアクション集計結果"
    )

@app.route("/reaction_report", methods=["POST"])
def reaction_report():
    text = request.form.get("text", "")
    user_id = request.form.get("user_id")
    try:
        channel_id, message_ts = parse_slack_url(text)
        threading.Thread(target=generate_reaction_report, args=(channel_id, message_ts, user_id)).start()
        return jsonify(response_type="in_channel", text="📊 集計を開始しました！完了次第ファイルを投稿します。")
    except Exception as e:
        return jsonify(response_type="ephemeral", text=f"⚠️ エラー: {e}")

@app.route("/slack/events", methods=["POST"])
def slack_events():
    payload = request.get_json()
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})

    event = payload.get("event", {})
    if event.get("type") == "reaction_added":
        user = event.get("user")
        channel = event.get("item", {}).get("channel")
        ts = event.get("item", {}).get("ts")
        try:
            generate_reaction_report(channel, ts, requested_by_user_id=user)
        except Exception as e:
            print(f"[ERROR] リアクション集計失敗: {e}")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
