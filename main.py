import os
import pandas as pd
from slack_sdk import WebClient

SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
MESSAGE_TS = os.environ["MESSAGE_TS"]

client = WebClient(token=SLACK_TOKEN)

# チャンネルメンバー取得
users = []
response = client.conversations_members(channel=CHANNEL_ID)
user_ids = response["members"]
for uid in user_ids:
    info = client.users_info(user=uid)
    if not info["user"]["is_bot"] and not info["user"]["deleted"]:
        users.append({"id": uid, "name": info["user"]["real_name"]})

# リアクション取得
response = client.reactions_get(channel=CHANNEL_ID, timestamp=MESSAGE_TS)
reactions = response["message"].get("reactions", [])
reaction_types = [r["name"] for r in reactions]

# 集計
data = []
user_id_to_name = {u["id"]: u["name"] for u in users}
for user in users:
    row = {"ユーザー名": user["name"]}
    for r in reaction_types:
        row[r] = 0
    data.append(row)

for r in reactions:
    name = r["name"]
    for u in r["users"]:
        user_name = user_id_to_name.get(u)
        if user_name:
            for row in data:
                if row["ユーザー名"] == user_name:
                    row[name] = 1

df = pd.DataFrame(data)
df.to_excel("reaction_report.xlsx", index=False)
print("✅ Excelファイルを出力しました。")

