# Slack Reaction Report Bot

Slackメッセージのリアクションを集計して、Excelで出力＆SlackにアップロードするBotです。

## セットアップ

1. `.env.sample` をコピーして `.env` を作成し、Slack Bot Token を設定
2. `pip install -r requirements.txt`
3. `python app.py` でローカル実行（開発用）

## デプロイ

Render.com にデプロイして Slashコマンド用Webhookとして利用します。

